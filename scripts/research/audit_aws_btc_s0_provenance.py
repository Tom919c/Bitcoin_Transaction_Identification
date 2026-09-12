#!/usr/bin/env python3
"""Gate 3A v1.3 label-free, resumable 1,000-event provenance audit."""
from __future__ import annotations

import argparse
import heapq
import hashlib
import json
import platform
import sqlite3
import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import extract_aws_btc_s0_events as extract
import audit_aws_btc_transaction_semantics as semantics
import freeze_aws_btc_transactions as freezer
from btcaml.data.script_identity import script_id

SAMPLE_TARGET = 1_000
FIRST_PER_CELL = 100
SUCCESS_THRESHOLD = 995
SALT = b"asof-audit-v1"
PROFILES = ("F_pub", "F_wide")
FROZEN_MANIFEST_SHA256 = "e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d"
FROZEN_TARGET_HEIGHT = 286_560
FROZEN_LAST_HEIGHT = 286_560
FROZEN_DESIGN = {
    "cutoff_heights": [181440, 199584, 215712, 225792], "window_blocks": 2016,
    "primary_horizon_blocks": 52560, "sensitivity_horizon_blocks": [13140, 105120],
    "eligible_end_height": 237731, "profiles": ["F_pub", "F_wide"],
    "diagnostic_profile": "F_none", "primary_metrics": ["p_merge", "p_rewrite"],
    "minimum_practical_difference": 0.01, "bootstrap_replicates": 10000,
    "bootstrap_block_lengths": [144, 72, 288],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ro_connect(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
        raise RuntimeError("S0 state must be read-only")
    if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise RuntimeError("S0 state quick_check failed")
    return connection


def load_summary(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("status") != "s0_union_extraction_complete":
        raise ValueError("completed extraction summary required")
    if value.get("s0_extraction_complete") is not True:
        raise ValueError("extraction summary is not complete")
    for key in ("source_manifest_sha256", "runner_sha256", "design", "s0_counters", "transaction_counters", "horizon_cells", "windows"):
        if not value.get(key):
            raise ValueError(f"summary lacks {key}")
    if value.get("effect_metrics_read") is not False or value.get("labels_read") is not False:
        raise ValueError("summary violates label/effect boundary")
    if value["source_manifest_sha256"] != FROZEN_MANIFEST_SHA256:
        raise ValueError("summary source manifest is not the frozen v1.1 manifest")
    if value.get("target_height") != FROZEN_TARGET_HEIGHT or value.get("last_complete_height") != FROZEN_LAST_HEIGHT:
        raise ValueError("summary does not cover the frozen S0 target")
    if value["design"] != FROZEN_DESIGN:
        raise ValueError("summary design differs from frozen Gate 3A design")
    expected_cells = extract.horizon_cells(FROZEN_DESIGN, 290291)
    if value["horizon_cells"] != expected_cells or len(expected_cells) != 12:
        raise ValueError("summary horizon cells differ from the frozen 12-cell design")
    if [cell["available"] for cell in expected_cells if cell["horizon_blocks"] == 105120] != [True, False, False, False]:
        raise RuntimeError("frozen long-horizon availability changed")
    if value["windows"] != extract.build_windows(FROZEN_DESIGN):
        raise ValueError("summary windows differ from frozen four-cutoff design")
    return value


def state_bindings(connection: sqlite3.Connection, summary: dict) -> dict:
    context = connection.execute(
        "SELECT source_manifest_sha256, runner_sha256, target_height, design_json FROM run_context WHERE context_id=1"
    ).fetchone()
    if context is None:
        raise RuntimeError("S0 run_context missing")
    if context[0] != summary["source_manifest_sha256"] or context[1] != summary["runner_sha256"]:
        raise RuntimeError("summary/state source or runner binding mismatch")
    if context[2] != FROZEN_TARGET_HEIGHT or context[2] != summary.get("target_height") or json.loads(context[3]) != FROZEN_DESIGN:
        raise RuntimeError("summary/state design binding mismatch")
    if summary.get("models_authorized") is not False:
        raise RuntimeError("summary models_authorized must be false")
    metadata = {key: json.loads(value) for key, value in connection.execute("SELECT key,value FROM metadata")}
    if metadata.get("last_committed_height") != FROZEN_LAST_HEIGHT or metadata.get("last_committed_height") != summary.get("last_complete_height"):
        raise RuntimeError("summary/state checkpoint height mismatch")
    if metadata.get("s0_counters") != summary["s0_counters"] or metadata.get("counters") != summary["transaction_counters"]:
        raise RuntimeError("summary/state metadata counters mismatch")
    if metadata.get("counters", {}).get("blocks") != FROZEN_LAST_HEIGHT + 1:
        raise RuntimeError("state transaction counters do not cover frozen target")
    for table, counter in (("union_events", "union_events"), ("window_transactions", "window_transactions"), ("window_support", "window_support"), ("block_profile_stats", "block_profile_stat_rows")):
        expected = int(summary["s0_counters"].get(counter, -1))
        actual = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        if actual != expected:
            raise RuntimeError(f"summary/state {table} count mismatch")
    stats = connection.execute("SELECT COUNT(DISTINCT height),MIN(height),MAX(height),COUNT(DISTINCT filter_profile) FROM block_profile_stats").fetchone()
    if tuple(stats) != (FROZEN_LAST_HEIGHT + 1, 0, FROZEN_LAST_HEIGHT, 3):
        raise RuntimeError("state block profile stats do not cover frozen prefix/profiles")
    actual = int(connection.execute("SELECT COUNT(*) FROM union_events").fetchone()[0])
    return {"source_manifest_sha256": context[0], "runner_sha256": context[1], "union_events": actual}


class DSU:
    def __init__(self) -> None:
        self.parent: dict[bytes, bytes] = {}
    def find(self, value: bytes) -> bytes:
        self.parent.setdefault(value, value)
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value
    def union(self, left: bytes, right: bytes) -> None:
        left, right = self.find(left), self.find(right)
        if left != right:
            self.parent[max(left, right)] = min(left, right)


def event_rank(event_id: bytes) -> tuple[bytes, bytes]:
    return hashlib.sha256(event_id + SALT).digest(), event_id


def reverse_bytes(value: bytes) -> bytes:
    return bytes(255 - item for item in value)


def cells(summary: dict) -> list[dict]:
    design = summary["design"]
    return [
        {"window_id": f"t{cutoff}", "cutoff": cutoff, "future": cutoff + design["primary_horizon_blocks"], "profile": profile}
        for cutoff in design["cutoff_heights"] for profile in PROFILES
    ]


def candidates(connection: sqlite3.Connection, summary: dict) -> dict[tuple[str, str], list[sqlite3.Row]]:
    connection.row_factory = sqlite3.Row
    result: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for cell in cells(summary):
        dsu = DSU()
        excluded_column = "exclude_f_pub" if cell["profile"] == "F_pub" else "exclude_f_wide"
        for row in connection.execute(
            f"SELECT script_id_a,script_id_b FROM union_events WHERE height<=? AND {excluded_column}=0 ORDER BY height,tx_index,event_index,script_id_a,script_id_b", (cell["future"],)
        ):
            dsu.union(row[0], row[1])
        roots = {dsu.find(row[0]) for row in connection.execute("SELECT script_id FROM window_support WHERE window_id=?", (cell["window_id"],))}
        heap: list[tuple[bytes, bytes, sqlite3.Row]] = []
        for row in connection.execute(
            f"SELECT * FROM union_events WHERE height<=? AND {excluded_column}=0 ORDER BY height,tx_index,event_index,script_id_a,script_id_b", (cell["future"],)
        ):
            if dsu.find(row["script_id_a"]) not in roots and dsu.find(row["script_id_b"]) not in roots:
                continue
            rank, event_id = event_rank(row["event_id"])
            item = (reverse_bytes(rank), reverse_bytes(event_id), row)
            if len(heap) < SAMPLE_TARGET:
                heapq.heappush(heap, item)
            elif item[:2] > heap[0][:2]:
                heapq.heapreplace(heap, item)
        result[cell["window_id"], cell["profile"]] = sorted((item[2] for item in heap), key=lambda row: event_rank(row["event_id"]))
    return result


def allocate(candidates_by_cell: dict[tuple[str, str], list[sqlite3.Row]], target: int = SAMPLE_TARGET) -> list[tuple[tuple[str, str], sqlite3.Row]]:
    ordered = list(candidates_by_cell)
    selected: set[bytes] = set()
    output: list[tuple[tuple[str, str], sqlite3.Row]] = []
    positions = {cell: 0 for cell in ordered}
    for cell in ordered:
        for row in candidates_by_cell[cell]:
            positions[cell] += 1
            if row["event_id"] not in selected:
                selected.add(row["event_id"]); output.append((cell, row))
                if sum(item[0] == cell for item in output) == FIRST_PER_CELL: break
        if sum(item[0] == cell for item in output) != FIRST_PER_CELL:
            raise RuntimeError(f"candidate cell {cell} has fewer than {FIRST_PER_CELL} globally unique events")
    while len(output) < target:
        progressed = False
        for cell in ordered:
            values = candidates_by_cell[cell]
            while positions[cell] < len(values):
                row = values[positions[cell]]; positions[cell] += 1
                if row["event_id"] not in selected:
                    selected.add(row["event_id"]); output.append((cell, row)); progressed = True; break
            if len(output) == target: break
        if not progressed:
            raise RuntimeError(f"all candidate cells exhausted before {target} unique events")
    return output


def frozen_inputs(summary: dict, cache_dir: Path) -> tuple[list[dict], dict[str, dict]]:
    """Re-bind cache bytes to the source manifest before reading any Parquet row."""
    root = Path(__file__).resolve().parents[2]
    manifest_bytes, manifest = extract.validate_source_manifest(
        root / extract.DEFAULT_SOURCE_MANIFEST
    )
    if hashlib.sha256(manifest_bytes).hexdigest() != summary["source_manifest_sha256"]:
        raise RuntimeError("completed summary source manifest binding mismatch")
    extract.validate_reference_code(manifest, root)
    extract.validate_semantic_qualification(manifest)
    artifacts = {entry["role"]: entry for entry in extract.validate_frozen_artifacts(manifest, root)}
    required = {"selected object listing", "transaction byte freeze", "transaction schema audit"}
    if not required <= set(artifacts):
        raise RuntimeError("source manifest lacks frozen transaction artifacts")
    listing = root / artifacts["selected object listing"]["path"]
    freeze = root / artifacts["transaction byte freeze"]["path"]
    schema = root / artifacts["transaction schema audit"]["path"]
    _, _, items, _, freeze_value, _, schema_value = semantics.verify_freeze_and_schema(
        listing, artifacts["selected object listing"]["sha256"], freeze, schema
    )
    return items, semantics.verify_transaction_files(items, freeze_value, schema_value, cache_dir)


def _record_matches(event: sqlite3.Row, row: dict) -> bool:
    evidence = json.loads(event["evidence_json"])
    return (
        row["height"] == event["height"] and row["position"] == event["tx_index"]
        and row["txid"] == event["txid"] and row["block_hash"] == event["block_hash"]
        and row["source"] == evidence["source"]
    )


def scan_and_recompute(
    connection: sqlite3.Connection, selection: list[tuple[tuple[str, str], sqlite3.Row]],
    items: list[dict], schema_by_key: dict[str, dict], cache_dir: Path, checkpoint: sqlite3.Connection,
    manifest_sha256: str,
) -> tuple[dict[bytes, tuple[bool, str]], dict[str, int]]:
    """Locate sources first; then make one full frozen scan of requested parents only."""
    def columns_for(key: str) -> list[str]:
        return extract.BASE_PARQUET_COLUMNS + (extract.INPUT_PARQUET_COLUMNS if schema_by_key[key]["inputs_present"] else [])
    def source_key(value: str) -> str:
        marker = " height="
        if marker not in value: raise RuntimeError("evidence source has no object/position identity")
        return value.split(marker, 1)[0]
    by_key = {str(item["key"]): item for item in items}
    events_by_key: dict[str, list[sqlite3.Row]] = {}
    for _, event in selection:
        evidence = json.loads(event["evidence_json"])
        required = {"heuristic_id", "source", "anchor_input_indices", "member_input_indices", "f_pub_matches", "d_wp100k_matches", "d_tx0_paper"}
        if set(evidence) != required or evidence["heuristic_id"] != extract.HEURISTIC_ID:
            raise RuntimeError("event evidence fields differ from frozen schema")
        events_by_key.setdefault(source_key(evidence["source"]), []).append(event)
    found: dict[bytes, dict] = {}; requested: set[tuple[bytes, int]] = set()
    counts = {"source_objects": 0, "parent_objects": 0, "rows": 0, "matched_transactions": 0, "parent_outputs": 0}
    for key, events in events_by_key.items():
        item = by_key.get(key)
        if item is None: raise RuntimeError("evidence source object absent from frozen listing")
        matches: dict[bytes, int] = {event["event_id"]: 0 for event in events}
        parquet = pq.ParquetFile(freezer.source.cache_path(cache_dir, item))
        for batch in parquet.iter_batches(batch_size=8192, columns=columns_for(key)):
            for raw in batch.to_pylist():
                row = semantics.compact_row(raw, freezer.source.parse_partition_date(key), key)
                matched = False
                for event in events:
                    if _record_matches(event, row):
                        matches[event["event_id"]] += 1; found[event["event_id"]] = row; matched = True
                counts["matched_transactions"] += int(matched)
        if any(value != 1 for value in matches.values()): raise RuntimeError("source event did not locate exactly one frozen transaction")
        for row in (found[event["event_id"]] for event in events):
            requested.update((value["parent_txid"], value["parent_vout"]) for value in row["inputs"])
        counts["source_objects"] += 1
    requested_txids = {value[0] for value in requested}
    start = int(json.loads(checkpoint.execute("SELECT value FROM metadata WHERE key='parent_object_index'").fetchone()[0])) if checkpoint.execute("SELECT 1 FROM metadata WHERE key='parent_object_index'").fetchone() else 0
    ordered_items = sorted(items, key=lambda value: str(value["key"]))
    for number, item in enumerate(ordered_items):
        if number < start: continue
        key = str(item["key"]); parquet = pq.ParquetFile(freezer.source.cache_path(cache_dir, item)); rows_read = 0
        for batch in parquet.iter_batches(batch_size=8192, columns=columns_for(key)):
            for raw in batch.to_pylist():
                rows_read += 1
                # Avoid parsing any non-requested transaction beyond its txid field.
                txid = semantics.normalize_hex(raw.get("txid"), f"{key}.txid", length=32)
                if txid not in requested_txids: continue
                row = semantics.compact_row(raw, freezer.source.parse_partition_date(key), key)
                for output in row["outputs"]:
                    outpoint = (row["txid"], output["index"])
                    if outpoint in requested:
                        inserted = checkpoint.execute("INSERT OR IGNORE INTO parent_outputs VALUES(?,?,?,?,?,?)", (row["txid"], output["index"], row["height"], row["position"], output["script"], output["value_sat"]))
                        if inserted.rowcount != 1:
                            raise RuntimeError("duplicate parent output version")
        if rows_read != int(schema_by_key[key]["rows"]): raise RuntimeError(f"Parquet row count changed: {key}")
        prior_rows = checkpoint.execute("SELECT value FROM metadata WHERE key='parent_rows_verified_total'").fetchone()
        total_rows = (json.loads(prior_rows[0]) if prior_rows else 0) + rows_read
        checkpoint.execute("INSERT OR REPLACE INTO metadata VALUES('parent_object_index',?)", (canonical(number + 1).decode(),))
        checkpoint.execute("INSERT OR REPLACE INTO metadata VALUES('parent_rows_verified_total',?)", (canonical(total_rows).decode(),)); checkpoint.commit()
        counts["parent_objects"] += 1; counts["rows"] += rows_read
    results: dict[bytes, tuple[bool, str]] = {}
    for _, event in selection:
        row = found[event["event_id"]]
        evidence = json.loads(event["evidence_json"])
        try:
            input_scripts = []
            for value in sorted(row["inputs"], key=lambda item: item["index"]):
                parent = checkpoint.execute(
                    "SELECT script,value_sat FROM parent_outputs WHERE txid=? AND vout=? "
                    "AND (created_height < ? OR (created_height = ? AND created_index < ?)) "
                    "ORDER BY created_height DESC,created_index DESC LIMIT 1",
                    (value["parent_txid"], value["parent_vout"], row["height"], row["height"], row["position"]),
                ).fetchone()
                if parent is None: raise RuntimeError("parent_output_missing")
                if parent[1] != value["value_sat"]: raise RuntimeError("parent_value_mismatch")
                input_scripts.append(bytes.fromhex(script_id(parent[0])))
            facts = extract.transaction_profile_facts(row, input_scripts)
            triples = facts["triples"]
            event_index = event["event_index"]
            if event_index >= len(triples): raise RuntimeError("event_index_missing")
            anchor, member, member_indices = triples[event_index]
            recomputed = extract.compute_event_id(manifest_sha256, row["block_hash"], row["height"], row["txid"], row["position"], event_index, anchor, member, extract.HEURISTIC_VERSION)
            if recomputed != event["event_id"] or anchor != event["script_id_a"] or member != event["script_id_b"]:
                raise RuntimeError("event_endpoint_mismatch")
            if member_indices != evidence["member_input_indices"]:
                raise RuntimeError("member_indices_mismatch")
            expected_anchor = [i for i, value in enumerate(input_scripts) if value == anchor]
            if expected_anchor != evidence["anchor_input_indices"]:
                raise RuntimeError("anchor_indices_mismatch")
            if list(facts["f_pub_matches"]) != evidence["f_pub_matches"]:
                raise RuntimeError("filter_evidence_mismatch")
            if list(facts["d_wp100k_matches"]) != evidence.get("d_wp100k_matches"):
                raise RuntimeError("wp100k_evidence_mismatch")
            if bool(facts["d_tx0_paper"]) != evidence.get("d_tx0_paper"):
                raise RuntimeError("tx0_evidence_mismatch")
            if int(facts["exclude_f_pub"]) != event["exclude_f_pub"] or int(facts["exclude_f_wide"]) != event["exclude_f_wide"]:
                raise RuntimeError("filter_decision_mismatch")
            results[event["event_id"]] = True, "recovered"
        except RuntimeError as error:
            results[event["event_id"]] = False, str(error)
    counts["parent_outputs"] = int(checkpoint.execute("SELECT COUNT(*) FROM parent_outputs").fetchone()[0])
    return results, counts


def open_checkpoint(path: Path, bindings: dict) -> sqlite3.Connection:
    existed = path.exists(); path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL"); connection.execute("PRAGMA synchronous=FULL")
    connection.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL) WITHOUT ROWID")
    connection.execute("CREATE TABLE IF NOT EXISTS events(event_id BLOB PRIMARY KEY,assigned_cell TEXT NOT NULL,ok INTEGER NOT NULL,reason TEXT NOT NULL) WITHOUT ROWID")
    connection.execute("CREATE TABLE IF NOT EXISTS parent_outputs(txid BLOB NOT NULL,vout INTEGER NOT NULL,created_height INTEGER NOT NULL,created_index INTEGER NOT NULL,script BLOB NOT NULL,value_sat INTEGER NOT NULL,PRIMARY KEY(txid,vout,created_height,created_index)) WITHOUT ROWID")
    stored = connection.execute("SELECT value FROM metadata WHERE key='bindings'").fetchone()
    encoded = canonical(bindings).decode()
    if stored and stored[0] != encoded: raise RuntimeError("checkpoint bindings differ")
    connection.execute("INSERT OR REPLACE INTO metadata VALUES('bindings',?)", (encoded,)); connection.commit()
    return connection


def pending_selection(
    checkpoint: sqlite3.Connection,
    selection: list[tuple[tuple[str, str], sqlite3.Row]],
) -> list[tuple[tuple[str, str], sqlite3.Row]]:
    """Resume only events not durably recorded under the bound selection."""
    return [
        item for item in selection
        if checkpoint.execute("SELECT 1 FROM events WHERE event_id=?", (item[1]["event_id"],)).fetchone() is None
    ]


def integrity_passed(recovered: int, target: int = SAMPLE_TARGET) -> bool:
    """Protocol threshold is meaningful only for the fixed 1,000-event audit."""
    return target == SAMPLE_TARGET and recovered >= SUCCESS_THRESHOLD


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--completed-extraction-summary"); p.add_argument("--s0-state-db")
    p.add_argument("--transaction-cache-dir"); p.add_argument("--output"); p.add_argument("--temporary-state-db")
    p.add_argument("--self-test", action="store_true"); return p


def self_test() -> None:
    connection = sqlite3.connect(":memory:"); connection.row_factory = sqlite3.Row
    extract.create_s0_schema(connection)
    design = {"cutoff_heights": [1, 2, 3, 4], "primary_horizon_blocks": 1, "profiles": ["F_pub", "F_wide"]}
    connection.execute("INSERT INTO run_context VALUES(1,1,'common-input','gate3a-v1.0-common-input-star','v','a'*64,'b'*64,5,?)", (canonical(design).decode(),))
    for window in ("t1", "t2", "t3", "t4"):
        connection.execute("INSERT INTO window_support VALUES(?,?,0)", (window, b'a'*32))
    for number in range(850):
        event = number.to_bytes(32, 'big'); left = b'a'*32 if number % 2 else b'z'*32
        connection.execute("INSERT INTO union_events VALUES(?,?,?,?,?,?,?,?,?,?,?)", (event, b'h'*32, number % 5, number.to_bytes(32,'big'), 0, 0, left, b'b'*32, 0, 0, canonical({"heuristic_id":"common-input","source":"x","anchor_input_indices":[0],"member_input_indices":[1],"f_pub_matches":[]}).decode()))
    summary = {"design": design}; chosen = allocate(candidates(connection, summary), 800)
    assert len(chosen) == 800 and len({row['event_id'] for _, row in chosen}) == 800
    try: allocate({("t1","F_pub"): []}, 1)
    except RuntimeError: pass
    else: raise AssertionError("missing cell quota accepted")
    connection.close()


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test(); print(json.dumps({"self_test":"passed","effect_metrics_read":False,"s0_decision":None}, sort_keys=True)); return 0
    required = ["completed_extraction_summary", "s0_state_db", "transaction_cache_dir", "output", "temporary_state_db"]
    if missing := [name for name in required if not getattr(args, name)]: raise ValueError(f"missing required arguments: {missing}")
    output = Path(args.output)
    summary_path, state_path = Path(args.completed_extraction_summary), Path(args.s0_state_db)
    summary = load_summary(summary_path); connection = ro_connect(state_path)
    try:
        bindings = state_bindings(connection, summary)
        selection = allocate(candidates(connection, summary))
        selection_sha256 = hashlib.sha256(canonical([
            {"cell": "|".join(cell), "event_id": row["event_id"].hex()} for cell, row in selection
        ])).hexdigest()
        auditor_sha256 = digest(Path(__file__))
        state_db_sha256 = digest(state_path)
        checkpoint_bindings = {**bindings, "summary_sha256": digest(summary_path), "selection_sha256": selection_sha256, "auditor_sha256": auditor_sha256, "state_db_sha256": state_db_sha256}
        checkpoint = open_checkpoint(Path(args.temporary_state_db), checkpoint_bindings)
        try:
            items, schema_by_key = frozen_inputs(summary, Path(args.transaction_cache_dir).resolve())
            pending = pending_selection(checkpoint, selection)
            scan_counts = {"source_objects": 0, "parent_objects": 0, "rows": 0, "matched_transactions": 0, "parent_outputs": int(checkpoint.execute("SELECT COUNT(*) FROM parent_outputs").fetchone()[0])}
            if pending:
                recovered_values, scan_counts = scan_and_recompute(
                    connection, pending, items, schema_by_key,
                    Path(args.transaction_cache_dir).resolve(), checkpoint,
                    bindings["source_manifest_sha256"],
                )
            for cell, row in pending:
                if checkpoint.execute("SELECT 1 FROM events WHERE event_id=?", (row["event_id"],)).fetchone() is None:
                    ok, reason = recovered_values[row["event_id"]]
                    checkpoint.execute("INSERT INTO events VALUES(?,?,?,?)", (row["event_id"], "|".join(cell), int(ok), reason)); checkpoint.commit()
            parent_index = checkpoint.execute("SELECT value FROM metadata WHERE key='parent_object_index'").fetchone()
            verified_objects = json.loads(parent_index[0]) if parent_index else 0
            if verified_objects != len(items):
                raise RuntimeError("checkpoint parent-object coverage is incomplete")
            parent_rows = checkpoint.execute("SELECT value FROM metadata WHERE key='parent_rows_verified_total'").fetchone()
            verified_rows = json.loads(parent_rows[0]) if parent_rows else 0
            recovered = checkpoint.execute("SELECT COUNT(*) FROM events WHERE ok=1").fetchone()[0]
            outcomes = {bytes(row[0]): (row[1], bool(row[2]), row[3]) for row in checkpoint.execute("SELECT event_id,assigned_cell,ok,reason FROM events")}
            event_records = [
                {"event_id": event["event_id"].hex(), "rank": event_rank(event["event_id"])[0].hex(), "block_hash": event["block_hash"].hex(), "height": event["height"], "txid": event["txid"].hex(), "tx_index": event["tx_index"], "event_index": event["event_index"], "script_id_a": event["script_id_a"].hex(), "script_id_b": event["script_id_b"].hex(), "assigned_cell": outcomes[event["event_id"]][0], "recovered": outcomes[event["event_id"]][1], "reason": outcomes[event["event_id"]][2]}
                for _, event in sorted(selection, key=lambda item: item[1]["event_id"])
            ]
            result = {"schema_version":"aws-btc-s0-provenance-audit-v1", "status":"integrity_component_complete", "s0_decision":None, "effect_metrics_read":False, "labels_read":False, "models_authorized":False, "source_manifest_sha256":bindings["source_manifest_sha256"], "extraction_summary_sha256":digest(summary_path), "state_db_sha256":state_db_sha256, "auditor_sha256":auditor_sha256, "checkpoint_bindings_sha256":hashlib.sha256(canonical(checkpoint_bindings)).hexdigest(), "state_quick_check":"ok", "sample_target":SAMPLE_TARGET, "sampled_unique_events":len(selection), "fully_recovered":recovered, "minimum_required":SUCCESS_THRESHOLD, "threshold_passed": integrity_passed(recovered), "assigned_cells": {"|".join(cell): sum(item[0] == cell for item in selection) for cell in cells(summary)}, "events":event_records, "scan_counts_this_run":scan_counts, "parent_objects_verified_total":verified_objects, "parent_rows_verified_total":verified_rows, "temporary_state_db":str(Path(args.temporary_state_db).resolve()), "runtime":{"python":platform.python_version(),"argv":sys.argv[1:]}, "limitations":["This integrity component does not compute effects or decide S0.","Raw scripts remain only in local temporary audit state and are never emitted."]}
            freezer.source.atomic_write_new(output, canonical(result))
        finally: checkpoint.close()
    finally: connection.close()
    print(json.dumps({"status":"integrity_component_complete","output":str(output),"effect_metrics_read":False,"s0_decision":None}, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
