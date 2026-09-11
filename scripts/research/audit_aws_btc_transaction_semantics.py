#!/usr/bin/env python3
"""Qualify frozen AWS Bitcoin transactions by replaying exact UTXO semantics."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import platform
import shutil
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

import audit_aws_btc_transaction_schemas as schema_audit
import freeze_aws_btc_transactions as freezer
import preflight_aws_btc_prefix as source


SCHEMA_VERSION = 1
SATOSHIS_PER_BTC = 100_000_000
MAX_MONEY_SATS = 2_100_000_000_000_000
DEFAULT_RESERVE_GIB = 20
DEFAULT_BATCH_SIZE = 8_192
DEFAULT_CHECKPOINT_BLOCKS = 2_016
BASE_COLUMNS = [
    "txid",
    "hash",
    "block_hash",
    "block_number",
    "index",
    "input_count",
    "output_count",
    "is_coinbase",
    "output_value",
    "outputs",
    "date",
]


class SpaceStop(RuntimeError):
    """A resumable stop after the last complete block checkpoint."""


class OperatorPause(RuntimeError):
    """A deliberate resumable pause after a complete block."""


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> tuple[bytes, dict]:
    payload = path.read_bytes()
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload, parsed


def require_false_flags(payload: dict, label: str) -> None:
    for name in ("effect_metrics_read", "formal_gate", "s0_authorized"):
        if payload.get(name, False) is not False:
            raise ValueError(f"{label}.{name} must be false")


def normalize_hex(value: object, label: str, *, length: int | None = None) -> bytes:
    if not isinstance(value, str):
        raise RuntimeError(f"{label} must be a hexadecimal string")
    if len(value) % 2:
        raise RuntimeError(f"{label} must contain an even number of hexadecimal characters")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as error:
        raise RuntimeError(f"{label} is not valid hexadecimal") from error
    if length is not None and len(decoded) != length:
        raise RuntimeError(f"{label} must decode to {length} bytes")
    return decoded


def amount_to_sats(value: object, label: str) -> tuple[int, float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label} must be numeric")
    converted = float(value)
    if not math.isfinite(converted) or converted < 0:
        raise RuntimeError(f"{label} must be finite and nonnegative")
    scaled = converted * SATOSHIS_PER_BTC
    satoshis = round(scaled)
    residual = abs(scaled - satoshis)
    if residual >= 0.5:
        raise RuntimeError(f"{label} is not uniquely recoverable as integer satoshis")
    if satoshis < 0 or satoshis > MAX_MONEY_SATS:
        raise RuntimeError(f"{label} exceeds the frozen money range")
    return satoshis, residual


def integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RuntimeError(f"{label} must be an integer >= {minimum}")
    return value


def verify_freeze_and_schema(
    listing_path: Path,
    expected_listing_sha256: str,
    freeze_path: Path,
    schema_path: Path,
) -> tuple[bytes, dict, list[dict], bytes, dict, bytes, dict]:
    listing_bytes, listing, items = freezer.load_frozen_selection(
        listing_path, expected_listing_sha256
    )
    _, _, freeze_bytes, freeze = schema_audit.load_inputs(
        listing_path, expected_listing_sha256, freeze_path
    )
    schema_bytes, schema = load_json(schema_path, "schema audit")
    if schema.get("status") != "candidate_transaction_schema_audit_complete":
        raise ValueError("schema audit is not complete")
    if schema.get("listing_file_sha256") != expected_listing_sha256:
        raise ValueError("schema audit references a different listing")
    if schema.get("freeze_manifest_sha256") != hashlib.sha256(freeze_bytes).hexdigest():
        raise ValueError("schema audit references a different freeze manifest")
    if schema.get("object_count") != len(items):
        raise ValueError("schema audit object count differs from the frozen listing")
    require_false_flags(listing, "listing")
    require_false_flags(freeze, "freeze manifest")
    require_false_flags(schema, "schema audit")

    freeze_by_key = {record.get("key"): record for record in freeze["transaction_objects"]}
    schema_records = schema.get("transaction_objects")
    if not isinstance(schema_records, list):
        raise ValueError("schema audit transaction_objects must be a list")
    schema_by_key = {record.get("key"): record for record in schema_records}
    expected_keys = {item["key"] for item in items}
    if (
        len(freeze_by_key) != len(items)
        or len(schema_by_key) != len(items)
        or set(freeze_by_key) != expected_keys
        or set(schema_by_key) != expected_keys
    ):
        raise ValueError("freeze/schema object keys differ from the frozen selection")
    return listing_bytes, listing, items, freeze_bytes, freeze, schema_bytes, schema


def load_block_map(
    listing: dict,
    expected_listing_sha256: str,
    preflight_path: Path,
    expected_preflight_sha256: str,
    block_cache_dir: Path,
    transaction_dates: set[str],
) -> tuple[dict[int, dict], dict]:
    preflight_bytes, preflight = load_json(preflight_path, "block preflight")
    actual_preflight_sha = hashlib.sha256(preflight_bytes).hexdigest()
    if actual_preflight_sha != expected_preflight_sha256:
        raise RuntimeError(
            f"block preflight SHA-256 mismatch: {actual_preflight_sha} != "
            f"{expected_preflight_sha256}"
        )
    if preflight.get("status") != "candidate_preflight_only":
        raise ValueError("block preflight is not complete")
    if preflight.get("listing_file_sha256") != expected_listing_sha256:
        raise ValueError("block preflight references a different listing")
    require_false_flags(preflight, "block preflight")

    selected = source.validate_object_list(
        listing["selected_block_objects"],
        f"{source.ROOT}/blocks/",
        "selected block objects",
    )
    records = preflight.get("block_objects")
    if not isinstance(records, list):
        raise ValueError("block preflight block_objects must be a list")
    by_key = {record.get("key"): record for record in records}
    if len(by_key) != len(selected) or set(by_key) != {item["key"] for item in selected}:
        raise ValueError("block preflight objects differ from the frozen selection")

    all_rows: list[dict] = []
    for number, item in enumerate(selected, start=1):
        record = by_key[item["key"]]
        if source.object_identity(record) != source.object_identity(item):
            raise RuntimeError(f"block identity mismatch: {item['key']}")
        path = source.cache_path(block_cache_dir, item).resolve()
        if Path(str(record.get("cache_path", ""))).resolve() != path:
            raise RuntimeError(f"block cache path mismatch: {item['key']}")
        if not path.is_file() or path.stat().st_size != int(item["size"]):
            raise RuntimeError(f"block cache size mismatch: {item['key']}")
        payload = path.read_bytes()
        rows, metadata = source.block_rows(item, payload)
        expected_metadata = {
            key: record.get(key)
            for key in (
                "key",
                "size",
                "last_modified",
                "etag",
                "cache_identity",
                "local_sha256",
                "rows",
                "min_height",
                "max_height",
                "partition_date",
            )
        }
        if metadata != expected_metadata:
            raise RuntimeError(f"block metadata differs from preflight: {item['key']}")
        all_rows.extend(rows)
        if number == 1 or number % 250 == 0 or number == len(selected):
            print(f"verified block object {number}/{len(selected)}", file=sys.stderr)

    selection = listing["selection"]
    audit = source.audit_blocks(
        all_rows,
        str(selection["last_included_complete_date"]),
        str(selection["block_lookahead_boundary"]),
    )
    by_height = audit.pop("rows_by_height")
    if audit != preflight.get("block_audit"):
        raise RuntimeError("replayed block audit differs from frozen block preflight")
    parameters = listing["parameters"]
    cutoffs = source.calculate_cutoffs(
        by_height,
        int(audit["candidate_hmax"]),
        int(parameters["horizon_blocks"]),
        int(parameters["window_blocks"]),
    )
    if cutoffs != preflight.get("cutoffs"):
        raise RuntimeError("replayed cutoffs differ from frozen block preflight")
    if audit["post_boundary_partition_reversion_count"] != 0:
        raise RuntimeError("selected transaction dates do not form a contiguous block prefix")

    hmax = int(audit["candidate_hmax"])
    selected_date_heights = {
        height
        for height, row in by_height.items()
        if str(row["partition_date"]) in transaction_dates
    }
    expected_heights = set(range(hmax + 1))
    if selected_date_heights != expected_heights:
        raise RuntimeError("transaction partition dates do not map exactly to heights 0..hmax")
    expected_transactions = sum(
        int(by_height[height]["transaction_count"]) for height in range(hmax + 1)
    )
    return by_height, {
        "preflight_bytes": preflight_bytes,
        "preflight": preflight,
        "block_object_count": len(selected),
        "candidate_hmax": hmax,
        "expected_transactions": expected_transactions,
    }


def verify_transaction_files(
    items: list[dict],
    freeze: dict,
    schema: dict,
    cache_dir: Path,
) -> dict[str, dict]:
    freeze_by_key = {record["key"]: record for record in freeze["transaction_objects"]}
    schema_by_key = {record["key"]: record for record in schema["transaction_objects"]}
    for number, item in enumerate(items, start=1):
        key = str(item["key"])
        frozen = freeze_by_key[key]
        audited = schema_by_key[key]
        identity = source.object_identity(item)
        if source.object_identity(frozen) != identity or source.object_identity(audited) != identity:
            raise RuntimeError(f"transaction identity mismatch: {key}")
        path = source.cache_path(cache_dir, item).resolve()
        if Path(str(frozen.get("cache_path", ""))).resolve() != path:
            raise RuntimeError(f"transaction cache path mismatch: {key}")
        if not path.is_file() or path.stat().st_size != int(item["size"]):
            raise RuntimeError(f"transaction cache size mismatch: {key}")
        sidecar_path = source.cache_sidecar_path(path)
        _, sidecar = load_json(sidecar_path, f"transaction sidecar {key}")
        if sidecar.get("object_identity") != identity:
            raise RuntimeError(f"transaction sidecar identity mismatch: {key}")
        expected_sha = frozen.get("local_sha256")
        if (
            not isinstance(expected_sha, str)
            or sidecar.get("local_sha256") != expected_sha
            or audited.get("local_sha256") != expected_sha
        ):
            raise RuntimeError(f"transaction SHA binding mismatch: {key}")
        if file_sha256(path) != expected_sha:
            raise RuntimeError(f"transaction content SHA mismatch: {key}")
        if audited.get("cache_identity") != source.cache_identity(item):
            raise RuntimeError(f"transaction schema cache identity mismatch: {key}")
        if number == 1 or number % 50 == 0 or number == len(items):
            print(f"verified transaction object {number}/{len(items)}", file=sys.stderr)
    return schema_by_key


def default_counters() -> dict[str, int | float]:
    return {
        "blocks": 0,
        "transactions": 0,
        "coinbase_transactions": 0,
        "noncoinbase_transactions": 0,
        "inputs": 0,
        "outputs": 0,
        "duplicate_txid_instances": 0,
        "live_outpoints": 0,
        "peak_live_outpoints": 0,
        "max_amount_residual_sats": 0.0,
        "failures": 0,
        "recovery_count": 0,
    }


def create_state_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE utxo (
            txid BLOB NOT NULL,
            vout INTEGER NOT NULL,
            value_sat INTEGER NOT NULL,
            script BLOB NOT NULL,
            created_height INTEGER NOT NULL,
            created_index INTEGER NOT NULL,
            PRIMARY KEY (txid, vout)
        ) WITHOUT ROWID;
        CREATE TABLE seen_txids (
            txid BLOB PRIMARY KEY
        ) WITHOUT ROWID;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        ) WITHOUT ROWID;
        """
    )


def metadata_get(connection: sqlite3.Connection, key: str) -> str:
    row = connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    if row is None:
        raise RuntimeError(f"state database lacks metadata key {key}")
    return str(row[0])


def metadata_set(connection: sqlite3.Connection, key: str, value: object) -> None:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    connection.execute(
        "INSERT INTO metadata(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, encoded),
    )


def open_state(
    path: Path, bindings: dict, started_utc: str
) -> tuple[sqlite3.Connection, int, dict]:
    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute("PRAGMA cache_size=-262144")
    if not existed:
        create_state_schema(connection)
        counters = default_counters()
        metadata_set(connection, "bindings", bindings)
        metadata_set(connection, "started_utc", started_utc)
        metadata_set(connection, "last_committed_height", -1)
        metadata_set(connection, "counters", counters)
        connection.commit()
        return connection, -1, counters

    if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise RuntimeError("state database quick_check failed")
    if json.loads(metadata_get(connection, "bindings")) != bindings:
        raise RuntimeError("state database bindings differ from this run")
    last_height = int(json.loads(metadata_get(connection, "last_committed_height")))
    counters = json.loads(metadata_get(connection, "counters"))
    if set(counters) != set(default_counters()):
        raise RuntimeError("state database counters have an incompatible schema")
    counters["recovery_count"] = int(counters["recovery_count"]) + 1
    return connection, last_height, counters


def checkpoint(
    connection: sqlite3.Connection, height: int, counters: dict
) -> None:
    metadata_set(connection, "last_committed_height", height)
    metadata_set(connection, "counters", counters)
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def validate_checkpoint_state(
    connection: sqlite3.Connection,
    height: int,
    counters: dict,
    by_height: dict[int, dict],
) -> None:
    expected_blocks = height + 1
    if int(counters["blocks"]) != expected_blocks:
        raise RuntimeError("checkpoint block count disagrees with committed height")
    expected_transactions = sum(
        int(by_height[current]["transaction_count"]) for current in range(height + 1)
    )
    if int(counters["transactions"]) != expected_transactions:
        raise RuntimeError("checkpoint transaction count disagrees with committed block prefix")
    if int(counters["coinbase_transactions"]) != expected_blocks:
        raise RuntimeError("checkpoint coinbase count disagrees with committed block prefix")
    if int(counters["transactions"]) != (
        int(counters["coinbase_transactions"]) + int(counters["noncoinbase_transactions"])
    ):
        raise RuntimeError("checkpoint transaction subtype counts are inconsistent")
    live_count = int(connection.execute("SELECT COUNT(*) FROM utxo").fetchone()[0])
    if live_count != int(counters["live_outpoints"]):
        raise RuntimeError("checkpoint live outpoint count disagrees with SQLite state")
    seen_count = int(connection.execute("SELECT COUNT(*) FROM seen_txids").fetchone()[0])
    if seen_count + int(counters["duplicate_txid_instances"]) != expected_transactions:
        raise RuntimeError("checkpoint seen-txid count is inconsistent")
    maximum_created = connection.execute("SELECT MAX(created_height) FROM utxo").fetchone()[0]
    if maximum_created is not None and int(maximum_created) > height:
        raise RuntimeError("checkpoint contains an outpoint created after its committed height")


def update_residual(counters: dict, residual: float) -> None:
    counters["max_amount_residual_sats"] = max(
        float(counters["max_amount_residual_sats"]), residual
    )


def compact_row(row: dict, partition_date: str, object_key: str) -> dict:
    height = integer(row.get("block_number"), f"{object_key}.block_number")
    position = integer(row.get("index"), f"{object_key}.index")
    label = f"{object_key} height={height} index={position}"
    if row.get("date") != partition_date:
        raise RuntimeError(f"{label}.date differs from its object partition")
    if not isinstance(row.get("is_coinbase"), bool):
        raise RuntimeError(f"{label}.is_coinbase must be boolean")
    input_count = integer(row.get("input_count"), f"{label}.input_count")
    output_count = integer(row.get("output_count"), f"{label}.output_count")
    txid = normalize_hex(row.get("txid"), f"{label}.txid", length=32)
    witness_hash = normalize_hex(row.get("hash"), f"{label}.hash", length=32)
    block_hash = normalize_hex(row.get("block_hash"), f"{label}.block_hash", length=32)

    outputs_raw = row.get("outputs")
    if not isinstance(outputs_raw, list) or not outputs_raw:
        raise RuntimeError(f"{label}.outputs must be a nonempty list")
    outputs = []
    residuals: list[float] = []
    for output in outputs_raw:
        if not isinstance(output, dict):
            raise RuntimeError(f"{label}.outputs contains a non-object")
        value_sat, residual = amount_to_sats(output.get("value"), f"{label}.output.value")
        residuals.append(residual)
        outputs.append(
            {
                "index": integer(output.get("index"), f"{label}.output.index"),
                "value_sat": value_sat,
                "script": normalize_hex(output.get("script_hex"), f"{label}.output.script_hex"),
            }
        )
    output_value, residual = amount_to_sats(row.get("output_value"), f"{label}.output_value")
    residuals.append(residual)

    inputs_raw = row.get("inputs")
    if inputs_raw is None:
        inputs_raw = []
    if not isinstance(inputs_raw, list):
        raise RuntimeError(f"{label}.inputs must be a list or null")
    inputs = []
    for transaction_input in inputs_raw:
        if not isinstance(transaction_input, dict):
            raise RuntimeError(f"{label}.inputs contains a non-object")
        value_sat, residual = amount_to_sats(
            transaction_input.get("value"), f"{label}.input.value"
        )
        residuals.append(residual)
        inputs.append(
            {
                "index": integer(transaction_input.get("index"), f"{label}.input.index"),
                "parent_txid": normalize_hex(
                    transaction_input.get("spent_transaction_hash"),
                    f"{label}.input.spent_transaction_hash",
                    length=32,
                ),
                "parent_vout": integer(
                    transaction_input.get("spent_output_index"),
                    f"{label}.input.spent_output_index",
                ),
                "value_sat": value_sat,
            }
        )

    is_coinbase = row["is_coinbase"]
    if is_coinbase:
        input_value = None
        fee = None
        for name in ("input_value", "fee"):
            if row.get(name) is not None:
                _, residual = amount_to_sats(row[name], f"{label}.{name}")
                residuals.append(residual)
    else:
        input_value, residual = amount_to_sats(row.get("input_value"), f"{label}.input_value")
        residuals.append(residual)
        fee, residual = amount_to_sats(row.get("fee"), f"{label}.fee")
        residuals.append(residual)

    return {
        "height": height,
        "position": position,
        "txid": txid,
        "witness_hash": witness_hash,
        "block_hash": block_hash,
        "input_count": input_count,
        "output_count": output_count,
        "is_coinbase": is_coinbase,
        "input_value": input_value,
        "output_value": output_value,
        "fee": fee,
        "inputs": inputs,
        "outputs": outputs,
        "max_amount_residual_sats": max(residuals, default=0.0),
        "source": label,
    }


def validate_positions(values: list[dict], count: int, label: str) -> None:
    positions = sorted(integer(value.get("index"), f"{label}.index") for value in values)
    if len(values) != count or positions != list(range(count)):
        raise RuntimeError(f"{label} indexes are not the exact 0..count-1 permutation")


def process_transaction(
    connection: sqlite3.Connection, row: dict, counters: dict
) -> None:
    label = row["source"]
    update_residual(counters, row["max_amount_residual_sats"])
    validate_positions(row["outputs"], row["output_count"], f"{label}.outputs")
    validate_positions(row["inputs"], row["input_count"], f"{label}.inputs")
    if row["is_coinbase"] != (row["position"] == 0):
        raise RuntimeError(f"{label} coinbase flag disagrees with block position")
    if row["is_coinbase"] and row["input_count"] != 0:
        raise RuntimeError(f"{label} coinbase transaction has inputs")
    if not row["is_coinbase"] and row["input_count"] == 0:
        raise RuntimeError(f"{label} non-coinbase transaction has no inputs")

    insertion = connection.execute(
        "INSERT OR IGNORE INTO seen_txids(txid) VALUES (?)", (row["txid"],)
    )
    if insertion.rowcount == 0:
        live = connection.execute(
            "SELECT 1 FROM utxo WHERE txid = ? LIMIT 1", (row["txid"],)
        ).fetchone()
        if live is not None:
            raise RuntimeError(f"{label} repeats a txid with live historical outputs")
        counters["duplicate_txid_instances"] += 1

    input_total = 0
    spent_in_transaction: set[tuple[bytes, int]] = set()
    for transaction_input in sorted(row["inputs"], key=lambda value: value["index"]):
        outpoint = (transaction_input["parent_txid"], transaction_input["parent_vout"])
        if outpoint in spent_in_transaction:
            raise RuntimeError(f"{label} spends the same outpoint twice")
        spent_in_transaction.add(outpoint)
        parent = connection.execute(
            "SELECT value_sat, script, created_height, created_index FROM utxo "
            "WHERE txid = ? AND vout = ?",
            outpoint,
        ).fetchone()
        if parent is None:
            raise RuntimeError(f"{label} references a missing, spent, or forward prevout")
        parent_value = int(parent[0])
        parent_script = parent[1]
        parent_height = int(parent[2])
        parent_index = int(parent[3])
        if not isinstance(parent_script, bytes):
            raise RuntimeError(f"{label} live parent locking script is not bytes")
        if (parent_height, parent_index) >= (row["height"], row["position"]):
            raise RuntimeError(f"{label} references a non-earlier prevout")
        if parent_value != transaction_input["value_sat"]:
            raise RuntimeError(f"{label} input value differs from its live parent output")
        deleted = connection.execute(
            "DELETE FROM utxo WHERE txid = ? AND vout = ?", outpoint
        )
        if deleted.rowcount != 1:
            raise RuntimeError(f"{label} failed to consume exactly one live prevout")
        counters["live_outpoints"] -= 1
        input_total += parent_value

    output_total = sum(output["value_sat"] for output in row["outputs"])
    if output_total > MAX_MONEY_SATS or input_total > MAX_MONEY_SATS:
        raise RuntimeError(f"{label} transaction total exceeds the frozen money range")
    if output_total != row["output_value"]:
        raise RuntimeError(f"{label} output_value differs from reconstructed outputs")
    if not row["is_coinbase"]:
        if input_total != row["input_value"]:
            raise RuntimeError(f"{label} input_value differs from reconstructed inputs")
        if input_total != output_total + row["fee"]:
            raise RuntimeError(f"{label} violates value conservation")

    for output in sorted(row["outputs"], key=lambda value: value["index"]):
        try:
            connection.execute(
                "INSERT INTO utxo(txid, vout, value_sat, script, created_height, created_index) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    row["txid"],
                    output["index"],
                    output["value_sat"],
                    output["script"],
                    row["height"],
                    row["position"],
                ),
            )
        except sqlite3.IntegrityError as error:
            raise RuntimeError(f"{label} creates a colliding live outpoint") from error
        counters["live_outpoints"] += 1
        counters["peak_live_outpoints"] = max(
            int(counters["peak_live_outpoints"]), int(counters["live_outpoints"])
        )

    counters["transactions"] += 1
    counters["coinbase_transactions" if row["is_coinbase"] else "noncoinbase_transactions"] += 1
    counters["inputs"] += len(row["inputs"])
    counters["outputs"] += len(row["outputs"])


def process_block(
    connection: sqlite3.Connection,
    height: int,
    rows: list[dict],
    block: dict,
    counters: dict,
) -> None:
    expected_count = int(block["transaction_count"])
    if len(rows) != expected_count:
        raise RuntimeError(
            f"height {height} transaction count differs: {len(rows)} != {expected_count}"
        )
    rows.sort(key=lambda row: row["position"])
    if [row["position"] for row in rows] != list(range(expected_count)):
        raise RuntimeError(f"height {height} indexes are not the exact block permutation")
    expected_hash = bytes.fromhex(str(block["hash"]))
    for row in rows:
        if row["height"] != height or row["block_hash"] != expected_hash:
            raise RuntimeError(f"height {height} row block binding mismatch")
        process_transaction(connection, row, counters)
    counters["blocks"] += 1


def partition_plan(
    items: list[dict], by_height: dict[int, dict], committed_height: int
) -> list[dict]:
    items_by_date: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        items_by_date[source.parse_partition_date(str(item["key"]))].append(item)
    heights_by_date: dict[str, list[int]] = defaultdict(list)
    for height, block in by_height.items():
        heights_by_date[str(block["partition_date"])].append(int(height))

    groups = []
    for partition_date in sorted(items_by_date):
        heights = sorted(
            height for height in heights_by_date.get(partition_date, []) if height > committed_height
        )
        groups.append(
            {
                "date": partition_date,
                "items": sorted(items_by_date[partition_date], key=lambda item: str(item["key"])),
                "eligible_min": min(heights) if heights else math.inf,
            }
        )
    suffix_min = [math.inf] * (len(groups) + 1)
    for index in range(len(groups) - 1, -1, -1):
        suffix_min[index] = min(groups[index]["eligible_min"], suffix_min[index + 1])
    for index, group in enumerate(groups):
        group["flush_before"] = suffix_min[index + 1]
    return groups


def replay(
    connection: sqlite3.Connection,
    items: list[dict],
    schema_by_key: dict[str, dict],
    transaction_cache_dir: Path,
    by_height: dict[int, dict],
    hmax: int,
    committed_height: int,
    counters: dict,
    batch_size: int,
    checkpoint_blocks: int,
    reserve_bytes: int,
    state_db: Path,
    pause_after_height: int | None,
) -> int:
    if pause_after_height is not None and pause_after_height <= committed_height:
        raise OperatorPause(
            f"requested pause height {pause_after_height} is already committed"
        )
    groups = partition_plan(items, by_height, committed_height)
    buffer: dict[int, list[dict]] = defaultdict(list)
    next_height = committed_height + 1
    blocks_since_checkpoint = 0
    connection.execute("BEGIN IMMEDIATE")
    try:
        for group_number, group in enumerate(groups, start=1):
            partition_date = group["date"]
            if math.isinf(group["eligible_min"]):
                continue
            for item in group["items"]:
                key = str(item["key"])
                path = source.cache_path(transaction_cache_dir, item)
                schema_record = schema_by_key[key]
                columns = list(BASE_COLUMNS)
                if schema_record.get("inputs_present"):
                    columns.extend(["fee", "input_value", "inputs"])
                parquet = pq.ParquetFile(path)
                rows_read = 0
                for batch in parquet.iter_batches(batch_size=batch_size, columns=columns):
                    rows = batch.to_pylist()
                    rows_read += len(rows)
                    for raw_row in rows:
                        raw_height = integer(
                            raw_row.get("block_number"), f"{key}.block_number"
                        )
                        if raw_height <= committed_height:
                            continue
                        if raw_height > hmax:
                            raise RuntimeError(f"{key} contains height {raw_height} above hmax {hmax}")
                        row = compact_row(raw_row, partition_date, key)
                        block = by_height[row["height"]]
                        if str(block["partition_date"]) != partition_date:
                            raise RuntimeError(f"{row['source']} differs from block partition date")
                        buffer[row["height"]].append(row)
                if rows_read != int(schema_record["rows"]):
                    raise RuntimeError(f"{key} row count changed since schema audit")

            flush_before = group["flush_before"]
            if math.isinf(flush_before):
                flush_before = hmax + 1
            while next_height < min(int(flush_before), hmax + 1):
                rows = buffer.pop(next_height, None)
                if rows is None:
                    raise RuntimeError(f"height {next_height} is absent below the unread watermark")
                process_block(connection, next_height, rows, by_height[next_height], counters)
                blocks_since_checkpoint += 1
                low_space = shutil.disk_usage(state_db.parent).free < reserve_bytes
                operator_pause = (
                    pause_after_height is not None and next_height >= pause_after_height
                )
                if blocks_since_checkpoint >= checkpoint_blocks or low_space or operator_pause:
                    checkpoint(connection, next_height, counters)
                    print(
                        json.dumps(
                            {
                                "checkpoint_height": next_height,
                                "transactions": counters["transactions"],
                                "live_outpoints": counters["live_outpoints"],
                                "free_bytes": shutil.disk_usage(state_db.parent).free,
                            },
                            sort_keys=True,
                        ),
                        file=sys.stderr,
                        flush=True,
                    )
                    blocks_since_checkpoint = 0
                    if low_space:
                        raise SpaceStop(
                            f"free space fell below reserve after height {next_height}"
                        )
                    if operator_pause:
                        raise OperatorPause(f"paused after complete height {next_height}")
                    connection.execute("BEGIN IMMEDIATE")
                next_height += 1
            if group_number == 1 or group_number % 100 == 0 or group_number == len(groups):
                print(
                    f"read partition group {group_number}/{len(groups)}; next height {next_height}",
                    file=sys.stderr,
                    flush=True,
                )

        while next_height <= hmax:
            rows = buffer.pop(next_height, None)
            if rows is None:
                raise RuntimeError(f"height {next_height} is absent at final flush")
            process_block(connection, next_height, rows, by_height[next_height], counters)
            blocks_since_checkpoint += 1
            next_height += 1
        if buffer:
            raise RuntimeError(f"unflushed heights remain: {sorted(buffer)[:5]}")
        checkpoint(connection, hmax, counters)
        return hmax
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise


def state_size(path: Path) -> dict[str, int]:
    sizes = {}
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        sizes[candidate.name] = candidate.stat().st_size if candidate.exists() else 0
    sizes["total"] = sum(sizes.values())
    return sizes


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--listing")
    argument_parser.add_argument("--expected-listing-sha256", type=freezer.sha256_arg)
    argument_parser.add_argument("--transaction-freeze-manifest")
    argument_parser.add_argument("--schema-audit")
    argument_parser.add_argument("--block-preflight")
    argument_parser.add_argument("--expected-block-preflight-sha256", type=freezer.sha256_arg)
    argument_parser.add_argument("--transaction-cache-dir")
    argument_parser.add_argument("--block-cache-dir")
    argument_parser.add_argument("--state-db")
    argument_parser.add_argument("--output")
    argument_parser.add_argument(
        "--reserve-gib", type=freezer.nonnegative_int, default=DEFAULT_RESERVE_GIB
    )
    argument_parser.add_argument(
        "--batch-size", type=source.positive_int, default=DEFAULT_BATCH_SIZE
    )
    argument_parser.add_argument(
        "--checkpoint-blocks", type=source.positive_int, default=DEFAULT_CHECKPOINT_BLOCKS
    )
    argument_parser.add_argument("--pause-after-height", type=freezer.nonnegative_int)
    argument_parser.add_argument("--self-test", action="store_true")
    return argument_parser


def sample_row(
    txid: bytes,
    height: int,
    position: int,
    *,
    coinbase: bool,
    inputs: list[dict],
    value: int,
) -> dict:
    return {
        "height": height,
        "position": position,
        "txid": txid,
        "witness_hash": txid,
        "block_hash": bytes(32),
        "input_count": len(inputs),
        "output_count": 1,
        "is_coinbase": coinbase,
        "input_value": None if coinbase else sum(item["value_sat"] for item in inputs),
        "output_value": value,
        "fee": None if coinbase else sum(item["value_sat"] for item in inputs) - value,
        "inputs": inputs,
        "outputs": [{"index": 0, "value_sat": value, "script": b""}],
        "max_amount_residual_sats": 0.0,
        "source": f"test:{height}:{position}",
    }


def self_test() -> None:
    assert amount_to_sats(0.0, "zero")[0] == 0
    assert amount_to_sats(0.00000001, "one sat")[0] == 1
    assert amount_to_sats(0.1, "tenth")[0] == 10_000_000
    for bad in (-1.0, float("nan"), 0.000000005):
        try:
            amount_to_sats(bad, "bad")
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"invalid amount was accepted: {bad}")

    fixture_items = [
        {"key": f"v1.0/btc/transactions/date=2009-01-0{day}/x.parquet"}
        for day in (3, 4, 5)
    ]
    fixture_blocks = {
        0: {"partition_date": "2009-01-03"},
        1: {"partition_date": "2009-01-05"},
        2: {"partition_date": "2009-01-04"},
    }
    plan = partition_plan(fixture_items, fixture_blocks, -1)
    assert [group["flush_before"] for group in plan] == [1, 1, math.inf]
    assert all(
        plan[index]["flush_before"] <= plan[index + 1]["flush_before"]
        for index in range(len(plan) - 1)
    )

    connection = sqlite3.connect(":memory:")
    create_state_schema(connection)
    counters = default_counters()
    first = bytes.fromhex("01" * 32)
    second = bytes.fromhex("02" * 32)
    process_transaction(
        connection,
        sample_row(first, 0, 0, coinbase=True, inputs=[], value=5_000_000_000),
        counters,
    )
    spend = {
        "index": 0,
        "parent_txid": first,
        "parent_vout": 0,
        "value_sat": 5_000_000_000,
    }
    process_transaction(
        connection,
        sample_row(second, 1, 1, coinbase=False, inputs=[spend], value=4_999_999_000),
        counters,
    )
    process_transaction(
        connection,
        sample_row(first, 2, 0, coinbase=True, inputs=[], value=5_000_000_000),
        counters,
    )
    assert counters["duplicate_txid_instances"] == 1
    try:
        process_transaction(
            connection,
            sample_row(second, 3, 0, coinbase=True, inputs=[], value=5_000_000_000),
            counters,
        )
    except RuntimeError as error:
        assert "live historical outputs" in str(error)
    else:
        raise AssertionError("live duplicate txid was accepted")
    connection.close()

    checkpoint_connection = sqlite3.connect(":memory:")
    create_state_schema(checkpoint_connection)
    checkpoint_counters = default_counters()
    third = bytes.fromhex("03" * 32)
    fourth = bytes.fromhex("04" * 32)
    blocks = {
        0: {"transaction_count": 1, "hash": "00" * 32},
        1: {"transaction_count": 2, "hash": "00" * 32},
    }
    process_block(
        checkpoint_connection,
        0,
        [sample_row(first, 0, 0, coinbase=True, inputs=[], value=5_000_000_000)],
        blocks[0],
        checkpoint_counters,
    )
    process_block(
        checkpoint_connection,
        1,
        [
            sample_row(third, 1, 0, coinbase=True, inputs=[], value=5_000_000_000),
            sample_row(
                fourth,
                1,
                1,
                coinbase=False,
                inputs=[
                    {
                        "index": 0,
                        "parent_txid": first,
                        "parent_vout": 0,
                        "value_sat": 5_000_000_000,
                    }
                ],
                value=4_999_999_000,
            ),
        ],
        blocks[1],
        checkpoint_counters,
    )
    validate_checkpoint_state(
        checkpoint_connection, 1, checkpoint_counters, blocks
    )
    checkpoint_counters["live_outpoints"] += 1
    try:
        validate_checkpoint_state(
            checkpoint_connection, 1, checkpoint_counters, blocks
        )
    except RuntimeError as error:
        assert "live outpoint count" in str(error)
    else:
        raise AssertionError("tampered checkpoint counters were accepted")
    checkpoint_connection.close()


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        print(
            json.dumps(
                {
                    "self_test": "passed",
                    "network": "not_used",
                    "effect_metrics_read": False,
                    "s0_authorized": False,
                },
                sort_keys=True,
            )
        )
        return 0

    required = {
        "--listing": args.listing,
        "--expected-listing-sha256": args.expected_listing_sha256,
        "--transaction-freeze-manifest": args.transaction_freeze_manifest,
        "--schema-audit": args.schema_audit,
        "--block-preflight": args.block_preflight,
        "--expected-block-preflight-sha256": args.expected_block_preflight_sha256,
        "--transaction-cache-dir": args.transaction_cache_dir,
        "--block-cache-dir": args.block_cache_dir,
        "--state-db": args.state_db,
        "--output": args.output,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        raise ValueError(f"missing required arguments: {missing}")

    listing_path = Path(args.listing)
    freeze_path = Path(args.transaction_freeze_manifest)
    schema_path = Path(args.schema_audit)
    preflight_path = Path(args.block_preflight)
    transaction_cache_dir = Path(args.transaction_cache_dir).resolve()
    block_cache_dir = Path(args.block_cache_dir).resolve()
    state_db = Path(args.state_db).resolve()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    source.preflight_output_parent(output)
    source.preflight_output_parent(state_db)
    reserve_bytes = args.reserve_gib * source.GIB
    free_before = shutil.disk_usage(state_db.parent).free
    if free_before < reserve_bytes:
        raise SpaceStop(f"free space below {args.reserve_gib} GiB reserve before replay")

    (
        listing_bytes,
        listing,
        items,
        freeze_bytes,
        freeze,
        schema_bytes,
        schema,
    ) = verify_freeze_and_schema(
        listing_path,
        args.expected_listing_sha256,
        freeze_path,
        schema_path,
    )
    transaction_dates = {
        source.parse_partition_date(str(item["key"])) for item in items
    }
    by_height, block_info = load_block_map(
        listing,
        args.expected_listing_sha256,
        preflight_path,
        args.expected_block_preflight_sha256,
        block_cache_dir,
        transaction_dates,
    )
    if schema.get("row_count") != block_info["expected_transactions"]:
        raise RuntimeError(
            "schema row count differs from candidate block transaction total: "
            f"{schema.get('row_count')} != {block_info['expected_transactions']}"
        )
    schema_by_key = verify_transaction_files(items, freeze, schema, transaction_cache_dir)

    bindings = {
        "listing_sha256": hashlib.sha256(listing_bytes).hexdigest(),
        "transaction_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "schema_audit_sha256": hashlib.sha256(schema_bytes).hexdigest(),
        "block_preflight_sha256": hashlib.sha256(block_info["preflight_bytes"]).hexdigest(),
        "script_sha256": script_sha256(),
        "candidate_hmax": block_info["candidate_hmax"],
    }
    invocation_started = dt.datetime.now(dt.timezone.utc).isoformat()
    connection, committed_height, counters = open_state(
        state_db, bindings, invocation_started
    )
    try:
        if committed_height < -1 or committed_height > block_info["candidate_hmax"]:
            raise RuntimeError("state database committed height is outside the candidate prefix")
        validate_checkpoint_state(connection, committed_height, counters, by_height)
        final_height = replay(
            connection,
            items,
            schema_by_key,
            transaction_cache_dir,
            by_height,
            int(block_info["candidate_hmax"]),
            committed_height,
            counters,
            args.batch_size,
            args.checkpoint_blocks,
            reserve_bytes,
            state_db,
            args.pause_after_height,
        )
        if counters["transactions"] != block_info["expected_transactions"]:
            raise RuntimeError("replayed transaction count differs from the block manifest")
        if counters["blocks"] != block_info["candidate_hmax"] + 1:
            raise RuntimeError("replayed block count differs from the candidate prefix")
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("final state database quick_check failed")
        final_live = int(connection.execute("SELECT COUNT(*) FROM utxo").fetchone()[0])
        if final_live != counters["live_outpoints"]:
            raise RuntimeError("tracked live outpoint count differs from SQLite state")
        ended_utc = dt.datetime.now(dt.timezone.utc).isoformat()
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "candidate_transaction_semantic_source_qualification_complete",
            "candidate_scope": "aws_public_bitcoin_prefix_source_qualification_only",
            "source_qualification_passed": True,
            "bindings": bindings,
            "inputs": {
                "listing": str(listing_path.resolve()),
                "transaction_freeze_manifest": str(freeze_path.resolve()),
                "schema_audit": str(schema_path.resolve()),
                "block_preflight": str(preflight_path.resolve()),
                "transaction_cache_dir": str(transaction_cache_dir),
                "block_cache_dir": str(block_cache_dir),
            },
            "started_utc": json.loads(metadata_get(connection, "started_utc")),
            "ended_utc": ended_utc,
            "last_complete_height": final_height,
            "candidate_tip_hash": str(by_height[final_height]["hash"]),
            "transaction_objects": len(items),
            "block_objects": block_info["block_object_count"],
            "schema_variants": len(schema["schema_variant_counts"]),
            **counters,
            "state_database": {
                "path": str(state_db),
                "sizes": state_size(state_db),
                "quick_check": "ok",
            },
            "runtime": {
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "pyarrow_version": __import__("pyarrow").__version__,
                "sqlite_version": sqlite3.sqlite_version,
                "platform": platform.platform(),
                "batch_size": args.batch_size,
                "checkpoint_blocks": args.checkpoint_blocks,
                "reserve_gib": args.reserve_gib,
                "free_bytes_before": free_before,
                "free_bytes_after": shutil.disk_usage(state_db.parent).free,
                "argv": sys.argv[1:],
            },
            "full_transaction_rows_read": True,
            "labels_read": False,
            "effect_metrics_read": False,
            "formal_gate": False,
            "s0_authorized": False,
            "public_redistribution_authorized": False,
            "limitations": [
                "This closes only the transaction semantic source-qualification check.",
                "No labels, clustering effects, model outputs, or test metrics were read.",
                "Gate 3A v1.0 and S0 remain unauthorized until separately frozen.",
            ],
        }
        source.atomic_write_new(output, source.canonical_json(result))
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "output": str(output),
                    "blocks": counters["blocks"],
                    "transactions": counters["transactions"],
                    "duplicate_txid_instances": counters["duplicate_txid_instances"],
                    "live_outpoints": counters["live_outpoints"],
                    "effect_metrics_read": False,
                    "s0_authorized": False,
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SpaceStop as error:
        print(
            json.dumps(
                {
                    "status": "resumable_space_stop",
                    "error": str(error),
                    "effect_metrics_read": False,
                    "s0_authorized": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(3)
    except OperatorPause as error:
        print(
            json.dumps(
                {
                    "status": "resumable_operator_pause",
                    "message": str(error),
                    "effect_metrics_read": False,
                    "s0_authorized": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(4)
    except (
        ValueError,
        RuntimeError,
        FileExistsError,
        OSError,
        json.JSONDecodeError,
        sqlite3.Error,
    ) as error:
        print(
            json.dumps(
                {
                    "status": "semantic_source_qualification_failed",
                    "error": str(error),
                    "effect_metrics_read": False,
                    "s0_authorized": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)
