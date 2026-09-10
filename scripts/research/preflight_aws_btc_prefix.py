#!/usr/bin/env python3
"""Freeze and independently preflight an AWS public Bitcoin prefix.

This is a candidate-source qualification tool.  It is not a source adapter,
formal manifest, or effect-metric runner.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


BUCKET = "aws-public-blockchain"
REGION = "us-east-2"
ROOT = "v1.0/btc"
SCHEMA_VERSION = 1
DEFAULT_LIMIT_GIB = 50
DEFAULT_HORIZON = 52560
DEFAULT_WINDOW = 2016
DEFAULT_LOOKAHEAD = 7
GIB = 1024**3
GENESIS_HASH = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def script_sha256() -> str:
    return sha256_bytes(Path(__file__).read_bytes())


def canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def atomic_write_new(path: Path, payload: bytes) -> None:
    """Write once, atomically.  Refuse to overwrite a scientific artifact."""
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise FileExistsError(f"refusing to overwrite existing file: {path}") from error
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def parse_partition_date(key: str) -> str:
    marker = "date="
    if marker not in key:
        raise ValueError(f"object key has no date partition: {key}")
    value = key.split(marker, 1)[1].split("/", 1)[0]
    dt.date.fromisoformat(value)
    return value


def object_identity(item: dict[str, object]) -> dict[str, object]:
    required = ("key", "size", "last_modified", "etag")
    absent = [field for field in required if field not in item or item[field] in (None, "")]
    if absent:
        raise ValueError(f"object identity missing fields {absent}")
    key = item["key"]
    size = item["size"]
    modified = item["last_modified"]
    etag = item["etag"]
    if not isinstance(key, str) or not isinstance(modified, str) or not isinstance(etag, str):
        raise ValueError("object identity has non-string key, last_modified, or etag")
    if not isinstance(size, int) or size < 0:
        raise ValueError("object identity has invalid size")
    parsed_modified = dt.datetime.fromisoformat(modified.replace("Z", "+00:00"))
    if parsed_modified.tzinfo is None or parsed_modified.utcoffset() != dt.timedelta(0):
        raise ValueError("object identity last_modified must have a UTC zero offset")
    if not etag:
        raise ValueError("object identity has empty etag")
    return {"key": key, "size": size, "last_modified": modified, "etag": etag}


def validate_object_list(items: object, exact_prefix: str, label: str) -> list[dict[str, object]]:
    if not isinstance(items, list):
        raise ValueError(f"{label} must be a list")
    checked: list[dict[str, object]] = []
    seen_keys: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{label} contains a non-object identity")
        identity = object_identity(item)
        key = str(identity["key"])
        if not key.startswith(exact_prefix):
            raise ValueError(f"{label} key is outside exact prefix {exact_prefix}: {key}")
        if (
            re.fullmatch(re.escape(exact_prefix) + r"date=\d{4}-\d{2}-\d{2}/[^/]+\.parquet", key)
            is None
        ):
            raise ValueError(f"{label} key is not an exact daily Parquet object path: {key}")
        parse_partition_date(key)
        if key in seen_keys:
            raise ValueError(f"{label} repeats key (including conflicting revisions): {key}")
        seen_keys.add(key)
        checked.append(identity)
    return checked


def cache_identity(item: dict[str, object]) -> str:
    return sha256_bytes(canonical_json(object_identity(item)))


def object_url(key: str) -> str:
    return f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{urllib.parse.quote(key, safe='/=')}"


def fetch_bytes(url: str, attempts: int = 3, timeout_seconds: int = 90) -> bytes:
    last_error: BaseException | None = None
    request = urllib.request.Request(url, headers={"User-Agent": "btcaml-prefix-preflight/1"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt == attempts:
                break
            time.sleep(attempt)
    raise RuntimeError(
        f"download failed after {attempts} attempts: {url}: {last_error}"
    ) from last_error


def fetch_block_bytes(
    item: dict[str, object],
    attempts: int = 3,
    timeout_seconds: int = 90,
    opener=urllib.request.urlopen,
) -> bytes:
    """Fetch one frozen object revision; a precondition failure is never retried."""
    identity = object_identity(item)
    expected_etag = str(identity["etag"])
    request = urllib.request.Request(
        object_url(str(identity["key"])),
        headers={"User-Agent": "btcaml-prefix-preflight/1", "If-Match": f'"{expected_etag}"'},
    )
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            with opener(request, timeout=timeout_seconds) as response:
                response_etag = response.headers.get("ETag", "").strip().strip('"')
                if response_etag != expected_etag:
                    raise RuntimeError(
                        f"response ETag differs from frozen identity for {identity['key']}"
                    )
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 412:
                raise RuntimeError(
                    f"frozen ETag precondition failed for {identity['key']}"
                ) from error
            last_error = error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
        if attempt < attempts:
            time.sleep(attempt)
    raise RuntimeError(
        f"block download failed after {attempts} attempts: {identity['key']}: {last_error}"
    ) from last_error


def list_objects(prefix: str) -> list[dict[str, object]]:
    """Anonymous ListObjectsV2, used only by --freeze-listing."""
    items: list[dict[str, object]] = []
    token: str | None = None
    seen_tokens: set[str] = set()
    namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    while True:
        query = {"list-type": "2", "prefix": prefix}
        if token:
            query["continuation-token"] = token
        url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/?{urllib.parse.urlencode(query)}"
        root = ET.fromstring(fetch_bytes(url))
        for content in root.findall("s3:Contents", namespace):
            key = content.findtext("s3:Key", default="", namespaces=namespace)
            size_text = content.findtext("s3:Size", default="", namespaces=namespace)
            modified = content.findtext("s3:LastModified", default="", namespaces=namespace)
            etag = content.findtext("s3:ETag", default="", namespaces=namespace).strip().strip('"')
            try:
                item = object_identity(
                    {"key": key, "size": int(size_text), "last_modified": modified, "etag": etag}
                )
            except (TypeError, ValueError) as error:
                raise RuntimeError(f"invalid ListObjectsV2 item under {prefix}: {error}") from error
            parse_partition_date(item["key"])
            items.append(item)
        truncated = (
            root.findtext("s3:IsTruncated", default="false", namespaces=namespace).lower() == "true"
        )
        token = root.findtext("s3:NextContinuationToken", default="", namespaces=namespace)
        if not truncated:
            break
        if not token:
            raise RuntimeError("truncated ListObjectsV2 response lacks NextContinuationToken")
        if token in seen_tokens:
            raise RuntimeError("ListObjectsV2 continuation token loop")
        seen_tokens.add(token)
    if not items:
        raise RuntimeError(f"anonymous listing was empty for {prefix}")
    return sorted(items, key=lambda item: str(item["key"]))


def grouped_dates(items: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in items:
        checked = object_identity(item)
        groups[parse_partition_date(str(checked["key"]))].append(checked)
    return groups


def choose_transaction_prefix(
    transactions: list[dict[str, object]], limit_bytes: int, current_utc_date: str
) -> dict[str, object]:
    """Take whole completed dates only; never substitute a partial date/window."""
    current = dt.date.fromisoformat(current_utc_date)
    grouped = grouped_dates(transactions)
    used = 0
    included: list[str] = []
    first_excluded: str | None = None
    excluded_bytes: int | None = None
    bytes_if_included: int | None = None
    stop_reason = "all_completed_partitions_fit"
    for date_text in sorted(grouped):
        day = dt.date.fromisoformat(date_text)
        if day >= current:
            stop_reason = "current_utc_date_excluded"
            break
        day_bytes = sum(int(item["size"]) for item in grouped[date_text])
        if used + day_bytes > limit_bytes:
            first_excluded = date_text
            excluded_bytes = day_bytes
            bytes_if_included = used + day_bytes
            stop_reason = "byte_limit_before_complete_date"
            break
        used += day_bytes
        included.append(date_text)
    if not included:
        raise RuntimeError("byte limit cannot include one complete transaction partition")
    if first_excluded is None:
        raise RuntimeError(
            "no first excluded complete date was found; refuse an unbounded candidate prefix"
        )
    last_included = included[-1]
    return {
        "limit_bytes": limit_bytes,
        "current_utc_date_excluded": current_utc_date,
        "last_included_complete_date": last_included,
        "first_excluded_complete_date": first_excluded,
        "first_excluded_complete_date_bytes": excluded_bytes,
        "bytes_if_first_excluded_included": bytes_if_included,
        "selected_transaction_bytes": used,
        "stop_reason": stop_reason,
    }


def selected_through(items: list[dict[str, object]], last_date: str) -> list[dict[str, object]]:
    return [
        object_identity(item)
        for item in items
        if parse_partition_date(str(item["key"])) <= last_date
    ]


def listing_manifest(
    transactions: list[dict[str, object]],
    blocks: list[dict[str, object]],
    args: argparse.Namespace,
    started: str,
    ended: str,
    current_utc_date: str,
) -> dict[str, object]:
    transactions = validate_object_list(
        transactions, f"{ROOT}/transactions/", "transaction listing"
    )
    blocks = validate_object_list(blocks, f"{ROOT}/blocks/", "block listing")
    selection = choose_transaction_prefix(transactions, args.limit_gib * GIB, current_utc_date)
    last_day = str(selection["last_included_complete_date"])
    boundary = (dt.date.fromisoformat(last_day) + dt.timedelta(days=args.lookahead)).isoformat()
    selected_transactions = selected_through(transactions, last_day)
    selected_blocks = selected_through(blocks, boundary)
    if not selected_blocks:
        raise RuntimeError("no block objects selected through lookahead boundary")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen_listing_only",
        "candidate_scope": "aws_public_bitcoin_prefix_preflight_only",
        "listing_query": {
            "bucket": BUCKET,
            "region": REGION,
            "transaction_prefix": f"{ROOT}/transactions/",
            "block_prefix": f"{ROOT}/blocks/",
            "started_utc": started,
            "ended_utc": ended,
            "anonymous_list_objects_v2": True,
        },
        "script_sha256": script_sha256(),
        "parameters": {
            "limit_gib": args.limit_gib,
            "limit_bytes": args.limit_gib * GIB,
            "horizon_blocks": args.horizon,
            "window_blocks": args.window,
            "lookahead_days": args.lookahead,
        },
        "selection": {**selection, "block_lookahead_boundary": boundary},
        "transaction_listing": transactions,
        "block_listing": blocks,
        "selected_transaction_objects": selected_transactions,
        "selected_block_objects": selected_blocks,
        "effect_metrics_read": False,
        "formal_gate": False,
    }


def require_fields(payload: dict[str, object], fields: tuple[str, ...], label: str) -> None:
    absent = [field for field in fields if field not in payload]
    if absent:
        raise ValueError(f"{label} missing fields {absent}")


def parse_utc_timestamp(value: object, label: str) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a timestamp string")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValueError(f"{label} must include a UTC zero offset")
    return parsed.astimezone(dt.timezone.utc)


def validate_listing(manifest: object, args: argparse.Namespace) -> dict[str, object]:
    if not isinstance(manifest, dict):
        raise ValueError("listing must be a JSON object")
    require_fields(
        manifest,
        (
            "schema_version",
            "status",
            "candidate_scope",
            "script_sha256",
            "listing_query",
            "parameters",
            "selection",
            "transaction_listing",
            "block_listing",
            "selected_transaction_objects",
            "selected_block_objects",
            "effect_metrics_read",
            "formal_gate",
        ),
        "listing",
    )
    if manifest["schema_version"] != SCHEMA_VERSION or manifest["status"] != "frozen_listing_only":
        raise ValueError("listing schema/status is not a frozen listing produced by this tool")
    if manifest["candidate_scope"] != "aws_public_bitcoin_prefix_preflight_only":
        raise ValueError("listing candidate_scope is not the preflight-only scope")
    if manifest["effect_metrics_read"] is not False or manifest["formal_gate"] is not False:
        raise ValueError("listing incorrectly claims effect metrics or a formal gate")
    frozen_hash = manifest["script_sha256"]
    if (
        not isinstance(frozen_hash, str)
        or len(frozen_hash) != 64
        or any(char not in "0123456789abcdef" for char in frozen_hash)
    ):
        raise ValueError("listing has invalid script_sha256")
    query = manifest["listing_query"]
    if not isinstance(query, dict):
        raise ValueError("listing_query must be an object")
    require_fields(
        query,
        (
            "bucket",
            "region",
            "transaction_prefix",
            "block_prefix",
            "started_utc",
            "ended_utc",
            "anonymous_list_objects_v2",
        ),
        "listing_query",
    )
    if query["bucket"] != BUCKET or query["region"] != REGION:
        raise ValueError("listing_query bucket/region differs from this source")
    if (
        query["transaction_prefix"] != f"{ROOT}/transactions/"
        or query["block_prefix"] != f"{ROOT}/blocks/"
    ):
        raise ValueError("listing_query prefixes differ from this source")
    if query["anonymous_list_objects_v2"] is not True:
        raise ValueError("listing_query is not an anonymous ListObjectsV2 record")
    started_utc = parse_utc_timestamp(query["started_utc"], "listing_query.started_utc")
    ended_utc = parse_utc_timestamp(query["ended_utc"], "listing_query.ended_utc")
    if ended_utc < started_utc:
        raise ValueError("listing_query ended before it started")
    parameters = manifest["parameters"]
    if not isinstance(parameters, dict):
        raise ValueError("listing parameters must be an object")
    expected_parameters = {
        "limit_gib": args.limit_gib,
        "limit_bytes": args.limit_gib * GIB,
        "horizon_blocks": args.horizon,
        "window_blocks": args.window,
        "lookahead_days": args.lookahead,
    }
    if parameters != expected_parameters:
        raise ValueError("listing parameters do not match this stage-2 command")
    transactions = validate_object_list(
        manifest["transaction_listing"], f"{ROOT}/transactions/", "transaction listing"
    )
    blocks = validate_object_list(manifest["block_listing"], f"{ROOT}/blocks/", "block listing")
    selection = manifest["selection"]
    if not isinstance(selection, dict):
        raise ValueError("listing selection must be an object")
    require_fields(
        selection,
        (
            "limit_bytes",
            "current_utc_date_excluded",
            "last_included_complete_date",
            "first_excluded_complete_date",
            "first_excluded_complete_date_bytes",
            "bytes_if_first_excluded_included",
            "selected_transaction_bytes",
            "stop_reason",
            "block_lookahead_boundary",
        ),
        "listing selection",
    )
    if selection["current_utc_date_excluded"] != started_utc.date().isoformat():
        raise ValueError("selection current_utc_date_excluded differs from listing start UTC date")
    recomputed = choose_transaction_prefix(
        transactions, args.limit_gib * GIB, str(selection["current_utc_date_excluded"])
    )
    boundary = (
        dt.date.fromisoformat(str(recomputed["last_included_complete_date"]))
        + dt.timedelta(days=args.lookahead)
    ).isoformat()
    if selection != {**recomputed, "block_lookahead_boundary": boundary}:
        raise ValueError(
            "listing selection summary was tampered with or is inconsistent with its full listing"
        )
    selected_transactions = selected_through(
        transactions, str(recomputed["last_included_complete_date"])
    )
    selected_blocks = selected_through(blocks, boundary)
    supplied_transactions = validate_object_list(
        manifest["selected_transaction_objects"],
        f"{ROOT}/transactions/",
        "selected transaction objects",
    )
    supplied_blocks = validate_object_list(
        manifest["selected_block_objects"], f"{ROOT}/blocks/", "selected block objects"
    )
    if supplied_transactions != selected_transactions:
        raise ValueError("selected transaction identities disagree with frozen listing")
    if supplied_blocks != selected_blocks:
        raise ValueError("selected block identities disagree with frozen listing")
    return {
        "manifest": manifest,
        "transactions": transactions,
        "blocks": blocks,
        "selection": selection,
        "selected_blocks": selected_blocks,
    }


def cache_path(cache_dir: Path, item: dict[str, object]) -> Path:
    return cache_dir / f"{cache_identity(item)}.parquet"


def cache_sidecar_path(path: Path) -> Path:
    return path.with_suffix(".json")


def write_cache(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def cached_payload(path: Path, item: dict[str, object]) -> bytes | None:
    sidecar = cache_sidecar_path(path)
    if not path.exists() or not sidecar.exists() or path.stat().st_size != int(item["size"]):
        return None
    try:
        metadata = json.loads(sidecar.read_bytes())
        payload = path.read_bytes()
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict) or metadata.get("object_identity") != object_identity(item):
        return None
    if metadata.get("local_sha256") != sha256_bytes(payload):
        return None
    return payload


def normalize_hash(value: object, label: str, item: dict[str, object]) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{label} must be a string: {item['key']}")
    normalized = value.lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise RuntimeError(f"{label} must be a 64-character hexadecimal string: {item['key']}")
    return normalized


def get_block_object(
    item: dict[str, object], cache_dir: Path, downloader=fetch_block_bytes
) -> tuple[bytes, str, Path]:
    item = object_identity(item)
    path = cache_path(cache_dir, item)
    expected_size = int(item["size"])
    payload = cached_payload(path, item)
    if payload is not None:
        return payload, "reused", path
    payload = downloader(item)
    if len(payload) != expected_size:
        raise RuntimeError(
            f"download size mismatch for {item['key']}: {len(payload)} != {expected_size}"
        )
    write_cache(path, payload)
    write_cache(
        cache_sidecar_path(path),
        canonical_json({"object_identity": item, "local_sha256": sha256_bytes(payload)}),
    )
    return payload, "downloaded", path


def block_rows(
    item: dict[str, object], payload: bytes
) -> tuple[list[dict[str, object]], dict[str, object]]:
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("stage 2 requires pyarrow to read cached block Parquet files") from error
    import io

    try:
        parquet = pq.ParquetFile(io.BytesIO(payload))
    except Exception as error:
        raise RuntimeError(f"cannot open block Parquet object: {item['key']}") from error

    required = ["hash", "number", "transaction_count", "date"]
    missing = [column for column in required if column not in parquet.schema_arrow.names]
    if missing:
        raise RuntimeError(f"block object lacks required columns {missing}: {item['key']}")
    has_previous = "previousblockhash" in parquet.schema_arrow.names
    columns = required + (["previousblockhash"] if has_previous else [])
    try:
        table = parquet.read(columns=columns)
    except Exception as error:
        raise RuntimeError(f"cannot read block Parquet object: {item['key']}") from error
    try:
        rows = table.to_pylist()
    except Exception as error:
        raise RuntimeError(f"cannot decode block Parquet rows: {item['key']}") from error
    if not rows:
        raise RuntimeError(f"block object is empty: {item['key']}")
    partition_date = parse_partition_date(str(item["key"]))
    if not has_previous and any(row["number"] != 0 for row in rows):
        raise RuntimeError(f"non-genesis block object lacks previousblockhash: {item['key']}")
    converted: list[dict[str, object]] = []
    for row in rows:
        date_value = str(row["date"])
        if date_value != partition_date:
            raise RuntimeError(f"block row date disagrees with object partition for {item['key']}")
        number = row["number"]
        transaction_count = row["transaction_count"]
        if type(number) is not int or number < 0:
            raise RuntimeError(f"block number must be a nonnegative integer: {item['key']}")
        if type(transaction_count) is not int or transaction_count < 1:
            raise RuntimeError(f"transaction_count must be a positive integer: {item['key']}")
        block_hash = normalize_hash(row["hash"], "hash", item)
        previous = None
        if has_previous:
            previous_value = row["previousblockhash"]
            if previous_value is not None:
                previous = normalize_hash(previous_value, "previousblockhash", item)
            elif number > 0:
                raise RuntimeError(f"non-genesis block has null previousblockhash: {item['key']}")
        converted.append(
            {
                "height": number,
                "hash": block_hash,
                "previousblockhash": previous,
                "transaction_count": transaction_count,
                "partition_date": partition_date,
            }
        )
    metadata = {
        **object_identity(item),
        "cache_identity": cache_identity(item),
        "local_sha256": sha256_bytes(payload),
        "rows": len(converted),
        "min_height": min(int(row["height"]) for row in converted),
        "max_height": max(int(row["height"]) for row in converted),
        "partition_date": partition_date,
    }
    return converted, metadata


def audit_blocks(
    rows: list[dict[str, object]], last_day: str, lookahead_boundary: str
) -> dict[str, object]:
    by_height: dict[int, dict[str, object]] = {}
    for row in rows:
        height = int(row["height"])
        if height in by_height:
            raise RuntimeError(f"duplicate block height {height}")
        by_height[height] = row
    if not by_height:
        raise RuntimeError("no block rows")
    maximum = max(by_height)
    expected = set(range(maximum + 1))
    if set(by_height) != expected:
        missing = min(expected - set(by_height))
        raise RuntimeError(
            f"block heights are not continuous from genesis; first missing {missing}"
        )
    genesis = by_height[0]
    if str(genesis["hash"]) != GENESIS_HASH:
        raise RuntimeError("genesis hash mismatch")
    for height in range(1, maximum + 1):
        if by_height[height]["previousblockhash"] != by_height[height - 1]["hash"]:
            raise RuntimeError(f"previousblockhash mismatch at height {height}")
    later = [height for height, row in by_height.items() if str(row["partition_date"]) > last_day]
    if not later:
        raise RuntimeError("lookahead block selection has no post-cutoff boundary block")
    first_later = min(later)
    candidate_hmax = first_later - 1
    if candidate_hmax < 0:
        raise RuntimeError("candidate cutoff precedes genesis")
    if any(
        str(by_height[height]["partition_date"]) > last_day for height in range(candidate_hmax + 1)
    ):
        raise RuntimeError("candidate prefix contains a post-cutoff partition date")
    if str(by_height[candidate_hmax + 1]["partition_date"]) <= last_day:
        raise RuntimeError("candidate boundary is not the first post-cutoff partition date")
    if max(str(row["partition_date"]) for row in rows) > lookahead_boundary:
        raise RuntimeError("block rows exceed frozen lookahead boundary")
    reversions = sum(
        str(by_height[height]["partition_date"]) <= last_day
        for height in range(candidate_hmax + 1, maximum + 1)
    )
    return {
        "genesis_hash": str(genesis["hash"]),
        "max_loaded_height": maximum,
        "candidate_hmax": candidate_hmax,
        "candidate_tip_hash": str(by_height[candidate_hmax]["hash"]),
        "first_height_after_last_included_date": first_later,
        "post_boundary_partition_reversion_count": reversions,
        "tip_hash_loaded": str(by_height[maximum]["hash"]),
        "rows_by_height": by_height,
    }


def calculate_cutoffs(
    by_height: dict[int, dict[str, object]], hmax: int, horizon: int, window: int
) -> dict[str, object]:
    if hmax <= horizon:
        raise RuntimeError("candidate prefix is shorter than one horizon")
    eligible_end = hmax - horizon
    if eligible_end < window - 1:
        raise RuntimeError("eligible prefix is shorter than one complete alignment window")
    noncoinbase = [0]
    for height in range(eligible_end + 1):
        transaction_count = int(by_height[height]["transaction_count"])
        if transaction_count < 1:
            raise RuntimeError(f"transaction_count < 1 at height {height}")
        noncoinbase.append(noncoinbase[-1] + transaction_count - 1)
    targets = (20, 40, 60, 80)
    total = noncoinbase[-1]
    if total == 0:
        raise RuntimeError("eligible prefix has no non-coinbase transactions")
    first: list[int] = []
    aligned: list[int] = []
    previous = -1
    for target in targets:
        height = next(
            (
                index - 1
                for index, count in enumerate(noncoinbase)
                if index > 0 and count * 100 >= total * target
            ),
            None,
        )
        if height is None:
            raise RuntimeError(f"cannot reach {target}% non-coinbase transactions")
        candidate = (height // window) * window
        if candidate <= previous:
            candidate = previous + window
        if candidate < window - 1:
            raise RuntimeError(f"aligned {target}% cutoff lacks a complete alignment window")
        if candidate > eligible_end:
            raise RuntimeError(f"aligned {target}% cutoff lacks a complete horizon")
        first.append(height)
        aligned.append(candidate)
        previous = candidate
    return {
        "eligible_end": eligible_end,
        "eligible_noncoinbase_transactions": total,
        "first_reaching_heights": first,
        "aligned_cutoffs": aligned,
        "horizon_blocks": horizon,
        "window_blocks": window,
        "alignment_rule": "floor_to_window_then_advance_one_window_when_not_strictly_after_previous",
    }


def run_stage_two(args: argparse.Namespace) -> dict[str, object]:
    listing_path = Path(args.listing)
    listing_bytes = listing_path.read_bytes()
    validated = validate_listing(json.loads(listing_bytes), args)
    selection = validated["selection"]
    selected_blocks = validated["selected_blocks"]
    cache_dir = Path(args.cache_dir).resolve()
    all_rows: list[dict[str, object]] = []
    object_records: list[dict[str, object]] = []

    def process(item: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
        payload, status, local_path = get_block_object(item, cache_dir)
        rows, record = block_rows(item, payload)
        record["cache_status"] = status
        record["cache_path"] = str(local_path)
        return rows, record

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process, item) for item in selected_blocks]
        for index, future in enumerate(futures, start=1):
            rows, record = future.result()
            all_rows.extend(rows)
            object_records.append(record)
            print(
                f"processed block object {index}/{len(futures)}: {record['key']}", file=sys.stderr
            )
    object_records.sort(key=lambda record: str(record["key"]))
    cache_counts = {
        "downloaded": sum(record["cache_status"] == "downloaded" for record in object_records),
        "reused": sum(record["cache_status"] == "reused" for record in object_records),
    }
    audit = audit_blocks(
        all_rows,
        str(selection["last_included_complete_date"]),
        str(selection["block_lookahead_boundary"]),
    )
    cutoffs = calculate_cutoffs(
        audit.pop("rows_by_height"), audit["candidate_hmax"], args.horizon, args.window
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_preflight_only",
        "candidate_scope": "aws_public_bitcoin_prefix_preflight_only",
        "listing_file": str(listing_path.resolve()),
        "listing_file_sha256": sha256_bytes(listing_bytes),
        "frozen_listing_script_sha256": validated["manifest"]["script_sha256"],
        "current_script_sha256": script_sha256(),
        "command_parameters": {
            "listing": str(listing_path.resolve()),
            "cache_dir": str(cache_dir),
            "output": str(Path(args.output).resolve()),
            "limit_gib": args.limit_gib,
            "horizon_blocks": args.horizon,
            "window_blocks": args.window,
            "lookahead_days": args.lookahead,
            "workers": args.workers,
            "argv": sys.argv[1:],
        },
        "selection": selection,
        "block_objects": object_records,
        "cache_counts": cache_counts,
        "block_audit": audit,
        "cutoffs": cutoffs,
        "cache_dir": str(cache_dir),
        "effect_metrics_read": False,
        "formal_gate": False,
        "limitations": [
            "Frozen AWS object identities are source evidence, not an immutable formal data manifest.",
            "No effect metrics, labels, or model outputs were read by this preflight.",
            "This candidate qualification does not authorize an S0 adapter or close a formal research gate.",
        ],
    }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def workers(value: str) -> int:
    parsed = positive_int(value)
    if parsed > 8:
        raise argparse.ArgumentTypeError("must be <= 8")
    return parsed


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    mode = argument_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--freeze-listing",
        metavar="OUTPUT",
        help="anonymous listing snapshot; this is the listing-network stage",
    )
    mode.add_argument(
        "--listing",
        metavar="INPUT",
        help="frozen-listing execution; downloads selected blocks only and never relists",
    )
    argument_parser.add_argument("--cache-dir", help="stage-2 Parquet cache directory")
    argument_parser.add_argument("--output", help="stage-2 detailed JSON output")
    argument_parser.add_argument("--limit-gib", type=positive_int, default=DEFAULT_LIMIT_GIB)
    argument_parser.add_argument("--horizon", type=positive_int, default=DEFAULT_HORIZON)
    argument_parser.add_argument("--window", type=positive_int, default=DEFAULT_WINDOW)
    argument_parser.add_argument("--lookahead", type=positive_int, default=DEFAULT_LOOKAHEAD)
    argument_parser.add_argument("--workers", type=workers, default=4)
    argument_parser.add_argument(
        "--self-test",
        action="store_true",
        help="pure local checks; no network or Parquet dependency",
    )
    return argument_parser


def self_test() -> None:
    fixture = [
        {
            "key": "v1.0/btc/transactions/date=2009-01-03/a.parquet",
            "size": 2,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "a",
        },
        {
            "key": "v1.0/btc/transactions/date=2009-01-04/a.parquet",
            "size": 3,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "b",
        },
        {
            "key": "v1.0/btc/transactions/date=2009-01-05/a.parquet",
            "size": 7,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "c",
        },
    ]
    choice = choose_transaction_prefix(fixture, 5, "2009-01-06")
    assert choice["last_included_complete_date"] == "2009-01-04"
    assert choice["first_excluded_complete_date"] == "2009-01-05"
    assert choice["bytes_if_first_excluded_included"] == 12
    base = fixture[0]
    for field, replacement in (
        ("key", "x"),
        ("size", 9),
        ("last_modified", "2026-01-02T00:00:00.000Z"),
        ("etag", "z"),
    ):
        changed = dict(base)
        changed[field] = replacement
        assert cache_identity(base) != cache_identity(changed)
    for invalid_time in ("2026-01-01T00:00:00", "2026-01-01T08:00:00+08:00"):
        try:
            object_identity(dict(base, last_modified=invalid_time))
            raise AssertionError("non-UTC last_modified was accepted")
        except ValueError:
            pass
    for invalid_time in ("2026-01-01T00:00:00", "2026-01-01T08:00:00+08:00"):
        try:
            parse_utc_timestamp(invalid_time, "self-test")
            raise AssertionError("non-UTC listing timestamp was accepted")
        except ValueError:
            pass
    try:
        validate_object_list(
            [dict(base, key="v1.0/btc/transactions/date=2009-01-03/nested/a.parquet")],
            f"{ROOT}/transactions/",
            "self-test nested transaction key",
        )
        raise AssertionError("nested transaction object path was accepted")
    except ValueError:
        pass
    rows = {height: {"transaction_count": 2} for height in range(20)}
    cutoffs = calculate_cutoffs(rows, 19, 5, 2)
    assert cutoffs["eligible_end"] == 14
    assert cutoffs["eligible_noncoinbase_transactions"] == 15
    assert cutoffs["first_reaching_heights"] == [2, 5, 8, 11]
    assert cutoffs["aligned_cutoffs"] == [2, 4, 8, 10]
    same_window_rows = {height: {"transaction_count": 1} for height in range(41)}
    same_window_rows[15] = {"transaction_count": 101}
    same_window = calculate_cutoffs(same_window_rows, 40, 1, 8)
    assert same_window["first_reaching_heights"] == [15, 15, 15, 15]
    assert same_window["aligned_cutoffs"] == [8, 16, 24, 32]
    try:
        calculate_cutoffs(rows, 19, 5, 16)
        raise AssertionError("early cutoff without a complete alignment window was accepted")
    except RuntimeError:
        pass
    try:
        calculate_cutoffs(
            {0: {"transaction_count": 0}, 1: {"transaction_count": 1}, 2: {"transaction_count": 1}},
            2,
            1,
            1,
        )
        raise AssertionError("zero transaction_count was accepted")
    except RuntimeError:
        pass
    audit = audit_blocks(
        [
            {
                "height": 0,
                "hash": GENESIS_HASH,
                "previousblockhash": None,
                "transaction_count": 1,
                "partition_date": "2009-01-03",
            },
            {
                "height": 1,
                "hash": "one",
                "previousblockhash": GENESIS_HASH,
                "transaction_count": 1,
                "partition_date": "2009-01-03",
            },
            {
                "height": 2,
                "hash": "two",
                "previousblockhash": "one",
                "transaction_count": 1,
                "partition_date": "2009-01-04",
            },
        ],
        "2009-01-03",
        "2009-01-04",
    )
    assert audit["genesis_hash"] == GENESIS_HASH and audit["candidate_tip_hash"] == "one"
    reversion_audit = audit_blocks(
        [
            {
                "height": 0,
                "hash": GENESIS_HASH,
                "previousblockhash": None,
                "transaction_count": 1,
                "partition_date": "2009-01-03",
            },
            {
                "height": 1,
                "hash": "one",
                "previousblockhash": GENESIS_HASH,
                "transaction_count": 1,
                "partition_date": "2009-01-04",
            },
            {
                "height": 2,
                "hash": "two",
                "previousblockhash": "one",
                "transaction_count": 1,
                "partition_date": "2009-01-03",
            },
        ],
        "2009-01-03",
        "2009-01-04",
    )
    assert (
        reversion_audit["candidate_hmax"] == 0
        and reversion_audit["post_boundary_partition_reversion_count"] == 1
    )
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "new.json"
        atomic_write_new(path, b"{}")
        try:
            atomic_write_new(path, b"{}")
            raise AssertionError("existing output was overwritten")
        except FileExistsError:
            pass
        cache_item = {
            "key": "v1.0/btc/blocks/date=2009-01-03/cache.parquet",
            "size": 3,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "cache",
        }
        downloads: list[dict[str, object]] = []

        def local_downloader(item: dict[str, object]) -> bytes:
            downloads.append(item)
            return b"abc"

        payload, status, cached = get_block_object(cache_item, Path(directory), local_downloader)
        assert payload == b"abc" and status == "downloaded"
        write_cache(cached, b"xyz")
        _, status, cached = get_block_object(cache_item, Path(directory), local_downloader)
        assert status == "downloaded" and len(downloads) == 2
        write_cache(
            cache_sidecar_path(cached),
            canonical_json(
                {
                    "object_identity": dict(cache_item, etag="wrong"),
                    "local_sha256": sha256_bytes(b"abc"),
                }
            ),
        )
        _, status, _ = get_block_object(cache_item, Path(directory), local_downloader)
        assert status == "downloaded" and len(downloads) == 3

        class LocalResponse:
            def __init__(self, etag: str, payload: bytes) -> None:
                self.headers = {"ETag": etag}
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self) -> bytes:
                return self.payload

        request_headers: list[str | None] = []

        def matching_opener(request, timeout):
            request_headers.append(request.get_header("If-match"))
            return LocalResponse('"cache"', b"abc")

        assert fetch_block_bytes(cache_item, opener=matching_opener) == b"abc"
        assert request_headers == ['"cache"']
        try:
            fetch_block_bytes(
                cache_item, opener=lambda request, timeout: LocalResponse('"wrong"', b"abc")
            )
            raise AssertionError("mismatched response ETag was accepted")
        except RuntimeError:
            pass
        precondition_calls: list[int] = []

        def precondition_opener(request, timeout):
            precondition_calls.append(1)
            raise urllib.error.HTTPError(request.full_url, 412, "precondition", {}, None)

        try:
            fetch_block_bytes(cache_item, attempts=3, opener=precondition_opener)
            raise AssertionError("HTTP 412 was accepted")
        except RuntimeError:
            pass
        assert len(precondition_calls) == 1
    fake_args = argparse.Namespace(limit_gib=1, horizon=5, window=2, lookahead=1)
    block_fixture = [
        {
            "key": "v1.0/btc/blocks/date=2009-01-03/a.parquet",
            "size": 1,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "d",
        },
        {
            "key": "v1.0/btc/blocks/date=2009-01-04/a.parquet",
            "size": 1,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "e",
        },
        {
            "key": "v1.0/btc/blocks/date=2009-01-05/a.parquet",
            "size": 1,
            "last_modified": "2026-01-01T00:00:00.000Z",
            "etag": "f",
        },
    ]
    manifest_transactions = [dict(item, size=GIB) for item in fixture]
    manifest = listing_manifest(
        manifest_transactions,
        block_fixture,
        fake_args,
        "2009-01-06T00:00:00+00:00",
        "2009-01-06T00:00:01+00:00",
        "2009-01-06",
    )
    validate_listing(manifest, fake_args)
    tampered = json.loads(json.dumps(manifest))
    tampered["selection"]["last_included_complete_date"] = "2009-01-04"
    try:
        validate_listing(tampered, fake_args)
        raise AssertionError("tampered frozen listing was accepted")
    except ValueError:
        pass
    bad_current_date = json.loads(json.dumps(manifest))
    bad_current_date["selection"]["current_utc_date_excluded"] = "2009-01-07"
    try:
        validate_listing(bad_current_date, fake_args)
        raise AssertionError("selection date differing from query start was accepted")
    except ValueError:
        pass
    bad_scope = json.loads(json.dumps(manifest))
    bad_scope["candidate_scope"] = "formal_gate"
    try:
        validate_listing(bad_scope, fake_args)
        raise AssertionError("invalid candidate scope was accepted")
    except ValueError:
        pass
    wrong_block = json.loads(json.dumps(manifest))
    wrong_block["selected_block_objects"] = [fixture[0]]
    try:
        validate_listing(wrong_block, fake_args)
        raise AssertionError("transaction key in selected blocks was accepted")
    except ValueError:
        pass


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        print(
            json.dumps(
                {"self_test": "passed", "network": "not_used", "parquet": "not_used"},
                sort_keys=True,
            )
        )
        return 0
    if not args.freeze_listing and not args.listing:
        raise ValueError("choose exactly one of --freeze-listing or --listing")
    if args.freeze_listing:
        if args.cache_dir or args.output:
            raise ValueError("--cache-dir and --output are stage-2 options")
        output = Path(args.freeze_listing)
        if output.exists():
            raise FileExistsError(f"refusing to overwrite existing file: {output}")
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        current_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
        transactions = list_objects(f"{ROOT}/transactions/")
        blocks = list_objects(f"{ROOT}/blocks/")
        ended = dt.datetime.now(dt.timezone.utc).isoformat()
        manifest = listing_manifest(transactions, blocks, args, started, ended, current_date)
        atomic_write_new(output, canonical_json(manifest))
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "output": str(output),
                    "effect_metrics_read": False,
                    "formal_gate": False,
                },
                sort_keys=True,
            )
        )
        return 0
    if not args.cache_dir or not args.output:
        raise ValueError("--listing requires --cache-dir and --output")
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    result = run_stage_two(args)
    atomic_write_new(output, canonical_json(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(output),
                "block_objects_processed": len(result["block_objects"]),
                "block_objects_downloaded": result["cache_counts"]["downloaded"],
                "block_objects_reused": result["cache_counts"]["reused"],
                "effect_metrics_read": False,
                "formal_gate": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, FileExistsError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
