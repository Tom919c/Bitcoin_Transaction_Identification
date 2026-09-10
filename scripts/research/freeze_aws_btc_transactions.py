#!/usr/bin/env python3
"""Privately freeze the transaction bytes selected by an AWS BTC listing."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import preflight_aws_btc_prefix as source


SCHEMA_VERSION = 1
DEFAULT_RESERVE_GIB = 20


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha256_arg(value: str) -> str:
    normalized = value.lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise argparse.ArgumentTypeError("must be a 64-character SHA-256 hexadecimal string")
    return normalized


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def load_frozen_selection(path: Path, expected_sha256: str) -> tuple[bytes, dict, list[dict]]:
    payload = path.read_bytes()
    actual_sha256 = source.sha256_bytes(payload)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"listing SHA-256 mismatch: {actual_sha256} != {expected_sha256}"
        )
    manifest = json.loads(payload)
    parameters = manifest.get("parameters") if isinstance(manifest, dict) else None
    if not isinstance(parameters, dict):
        raise ValueError("listing lacks parameters")
    args = SimpleNamespace(
        limit_gib=parameters.get("limit_gib"),
        horizon=parameters.get("horizon_blocks"),
        window=parameters.get("window_blocks"),
        lookahead=parameters.get("lookahead_days"),
    )
    source.validate_listing(manifest, args)
    items = source.validate_object_list(
        manifest["selected_transaction_objects"],
        f"{source.ROOT}/transactions/",
        "selected transaction objects",
    )
    selected_bytes = sum(int(item["size"]) for item in items)
    if selected_bytes != manifest["selection"]["selected_transaction_bytes"]:
        raise RuntimeError("selected transaction byte total differs from listing summary")
    return payload, manifest, items


def looks_complete(path: Path, item: dict) -> bool:
    sidecar = source.cache_sidecar_path(path)
    if not path.is_file() or not sidecar.is_file() or path.stat().st_size != item["size"]:
        return False
    try:
        metadata = json.loads(sidecar.read_bytes())
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(metadata, dict):
        return False
    digest = metadata.get("local_sha256")
    return (
        metadata.get("object_identity") == source.object_identity(item)
        and isinstance(digest, str)
        and len(digest) == 64
        and all(char in "0123456789abcdef" for char in digest)
    )


def storage_plan(
    items: list[dict], cache_dir: Path, reserve_bytes: int, workers: int
) -> dict[str, int]:
    missing_bytes = 0
    apparent_complete_bytes = 0
    for item in items:
        size = int(item["size"])
        if looks_complete(source.cache_path(cache_dir, item), item):
            apparent_complete_bytes += size
        else:
            missing_bytes += size
    concurrent_temp_bytes = sum(
        sorted((int(item["size"]) for item in items), reverse=True)[:workers]
    )
    return {
        "selected_bytes": missing_bytes + apparent_complete_bytes,
        "apparent_complete_bytes": apparent_complete_bytes,
        "missing_bytes": missing_bytes,
        "concurrent_temp_bytes": concurrent_temp_bytes,
        "reserve_bytes": reserve_bytes,
        "required_free_bytes": missing_bytes + concurrent_temp_bytes + reserve_bytes,
    }


def freeze(items: list[dict], cache_dir: Path, workers: int) -> tuple[list[dict], dict]:
    records: list[dict] = []

    def process(item: dict) -> dict:
        payload, status, path = source.get_block_object(item, cache_dir)
        return {
            **source.object_identity(item),
            "cache_identity": source.cache_identity(item),
            "cache_path": str(path.resolve()),
            "local_sha256": source.sha256_bytes(payload),
            "cache_status": status,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process, item): item for item in items}
        try:
            for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                record = future.result()
                records.append(record)
                if completed == 1 or completed % 10 == 0 or completed == len(futures):
                    print(
                        f"frozen transaction object {completed}/{len(futures)}: {record['key']}",
                        file=sys.stderr,
                        flush=True,
                    )
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    records.sort(key=lambda record: str(record["key"]))
    counts = {
        "downloaded": sum(record["cache_status"] == "downloaded" for record in records),
        "reused": sum(record["cache_status"] == "reused" for record in records),
    }
    return records, counts


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--listing")
    argument_parser.add_argument("--expected-listing-sha256", type=sha256_arg)
    argument_parser.add_argument("--cache-dir")
    argument_parser.add_argument("--output")
    argument_parser.add_argument(
        "--reserve-gib", type=nonnegative_int, default=DEFAULT_RESERVE_GIB
    )
    argument_parser.add_argument("--workers", type=source.workers, default=4)
    argument_parser.add_argument("--self-test", action="store_true")
    return argument_parser


def self_test() -> None:
    items = [
        {
            "key": "v1.0/btc/transactions/date=2009-01-03/a.parquet",
            "size": 3,
            "last_modified": "2026-01-01T00:00:00+00:00",
            "etag": "a",
        },
        {
            "key": "v1.0/btc/transactions/date=2009-01-04/a.parquet",
            "size": 5,
            "last_modified": "2026-01-01T00:00:00+00:00",
            "etag": "b",
        },
    ]
    with tempfile.TemporaryDirectory() as directory:
        cache_dir = Path(directory)
        empty = storage_plan(items, cache_dir, 7, 2)
        assert empty == {
            "selected_bytes": 8,
            "apparent_complete_bytes": 0,
            "missing_bytes": 8,
            "concurrent_temp_bytes": 8,
            "reserve_bytes": 7,
            "required_free_bytes": 23,
        }
        path = source.cache_path(cache_dir, items[0])
        source.write_cache(path, b"abc")
        source.write_cache(
            source.cache_sidecar_path(path),
            source.canonical_json(
                {
                    "object_identity": source.object_identity(items[0]),
                    "local_sha256": source.sha256_bytes(b"abc"),
                }
            ),
        )
        partial = storage_plan(items, cache_dir, 7, 2)
        assert partial["apparent_complete_bytes"] == 3
        assert partial["missing_bytes"] == 5
        assert partial["required_free_bytes"] == 20
        source.write_cache(source.cache_sidecar_path(path), b"{}")
        assert storage_plan(items, cache_dir, 7, 2) == empty


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"self_test": "passed", "network": "not_used"}, sort_keys=True))
        return 0
    required = {
        "--listing": args.listing,
        "--expected-listing-sha256": args.expected_listing_sha256,
        "--cache-dir": args.cache_dir,
        "--output": args.output,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        raise ValueError(f"missing required arguments: {missing}")

    listing_path = Path(args.listing)
    cache_dir = Path(args.cache_dir).resolve()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    source.preflight_output_parent(output)
    source.preflight_output_parent(cache_dir / "cache-write-check")
    listing_bytes, manifest, items = load_frozen_selection(
        listing_path, args.expected_listing_sha256
    )
    reserve_bytes = args.reserve_gib * source.GIB
    plan = storage_plan(items, cache_dir, reserve_bytes, args.workers)
    free_before = shutil.disk_usage(cache_dir).free
    if free_before < plan["required_free_bytes"]:
        raise RuntimeError(
            "insufficient free space before download: "
            f"{free_before} < {plan['required_free_bytes']}"
        )
    print(
        json.dumps({"storage_plan": plan, "free_bytes": free_before}, sort_keys=True),
        file=sys.stderr,
    )

    started = dt.datetime.now(dt.timezone.utc).isoformat()
    records, counts = freeze(items, cache_dir, args.workers)
    ended = dt.datetime.now(dt.timezone.utc).isoformat()
    if len(records) != len(items):
        raise RuntimeError(f"frozen object count mismatch: {len(records)} != {len(items)}")
    frozen_bytes = sum(int(record["size"]) for record in records)
    if frozen_bytes != manifest["selection"]["selected_transaction_bytes"]:
        raise RuntimeError("frozen transaction byte total differs from listing summary")
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "private_candidate_transaction_byte_freeze_complete",
        "candidate_scope": "aws_public_bitcoin_prefix_private_byte_freeze_only",
        "listing_file": str(listing_path.resolve()),
        "listing_file_sha256": source.sha256_bytes(listing_bytes),
        "listing_script_sha256": manifest["script_sha256"],
        "preflight_module_sha256": source.script_sha256(),
        "freezer_script_sha256": script_sha256(),
        "started_utc": started,
        "ended_utc": ended,
        "command_parameters": {
            "cache_dir": str(cache_dir),
            "output": str(output.resolve()),
            "reserve_gib": args.reserve_gib,
            "workers": args.workers,
            "argv": sys.argv[1:],
        },
        "storage_plan_before": plan,
        "free_bytes_before": free_before,
        "free_bytes_after": shutil.disk_usage(cache_dir).free,
        "selected_transaction_bytes": frozen_bytes,
        "transaction_objects": records,
        "cache_counts": counts,
        "private_internal_only": True,
        "public_redistribution_authorized": False,
        "parquet_rows_read": False,
        "effect_metrics_read": False,
        "formal_gate": False,
        "s0_authorized": False,
        "limitations": [
            "This artifact proves selected-object byte retention, not Parquet row integrity.",
            "Transaction uniqueness, prevout closure, integer-satoshi recovery and value "
            "conservation remain unaudited.",
            "No public redistribution of raw or reconstructed data is authorized by this run.",
        ],
    }
    source.atomic_write_new(output, source.canonical_json(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(output),
                "transaction_objects": len(records),
                "downloaded": counts["downloaded"],
                "reused": counts["reused"],
                "formal_gate": False,
                "s0_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
