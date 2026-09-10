#!/usr/bin/env python3
"""Audit frozen AWS Bitcoin transaction Parquet schemas before S0."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import freeze_aws_btc_transactions as freezer


SCHEMA_VERSION = 1
TOP_LEVEL_REQUIRED = {
    "txid",
    "hash",
    "block_hash",
    "block_number",
    "index",
    "input_count",
    "output_count",
    "is_coinbase",
    "outputs",
    "date",
}
OUTPUT_REQUIRED = {"index", "script_hex", "value"}
INPUT_REQUIRED = {
    "index",
    "spent_transaction_hash",
    "spent_output_index",
    "value",
}


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def list_struct_fields(field: pa.Field, label: str) -> dict[str, pa.Field]:
    value_type = field.type
    if not (pa.types.is_list(value_type) or pa.types.is_large_list(value_type)):
        raise RuntimeError(f"{label} must be a list, got {value_type}")
    value_type = value_type.value_type
    if not pa.types.is_struct(value_type):
        raise RuntimeError(f"{label} values must be structs, got {value_type}")
    return {child.name: child for child in value_type}


def validate_schema(schema: pa.Schema, label: str) -> bool:
    names = set(schema.names)
    missing = sorted(TOP_LEVEL_REQUIRED - names)
    if missing:
        raise RuntimeError(f"{label} lacks required columns {missing}")
    string_fields = ("txid", "hash", "block_hash", "date")
    integer_fields = ("block_number", "index", "input_count", "output_count")
    for name in string_fields:
        if not pa.types.is_string(schema.field(name).type):
            raise RuntimeError(f"{label}.{name} must be string")
    for name in integer_fields:
        if not pa.types.is_integer(schema.field(name).type):
            raise RuntimeError(f"{label}.{name} must be integer")
    if not pa.types.is_boolean(schema.field("is_coinbase").type):
        raise RuntimeError(f"{label}.is_coinbase must be boolean")

    outputs = list_struct_fields(schema.field("outputs"), f"{label}.outputs")
    missing_outputs = sorted(OUTPUT_REQUIRED - outputs.keys())
    if missing_outputs:
        raise RuntimeError(f"{label}.outputs lacks fields {missing_outputs}")
    if not pa.types.is_integer(outputs["index"].type):
        raise RuntimeError(f"{label}.outputs.index must be integer")
    if not pa.types.is_string(outputs["script_hex"].type):
        raise RuntimeError(f"{label}.outputs.script_hex must be string")
    if not pa.types.is_floating(outputs["value"].type):
        raise RuntimeError(f"{label}.outputs.value must be floating point")

    if "inputs" not in names:
        return False
    inputs = list_struct_fields(schema.field("inputs"), f"{label}.inputs")
    missing_inputs = sorted(INPUT_REQUIRED - inputs.keys())
    if missing_inputs:
        raise RuntimeError(f"{label}.inputs lacks fields {missing_inputs}")
    for name in ("index", "spent_output_index"):
        if not pa.types.is_integer(inputs[name].type):
            raise RuntimeError(f"{label}.inputs.{name} must be integer")
    if not pa.types.is_string(inputs["spent_transaction_hash"].type):
        raise RuntimeError(f"{label}.inputs.spent_transaction_hash must be string")
    if not pa.types.is_floating(inputs["value"].type):
        raise RuntimeError(f"{label}.inputs.value must be floating point")
    return True


def load_inputs(
    listing_path: Path,
    expected_listing_sha256: str,
    freeze_path: Path,
) -> tuple[bytes, list[dict], bytes, dict]:
    listing_bytes, _, items = freezer.load_frozen_selection(
        listing_path, expected_listing_sha256
    )
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    if not isinstance(freeze, dict):
        raise ValueError("freeze manifest must be an object")
    if freeze.get("status") != "private_candidate_transaction_byte_freeze_complete":
        raise ValueError("transaction byte freeze is not complete")
    if freeze.get("listing_file_sha256") != expected_listing_sha256:
        raise ValueError("freeze manifest references a different listing")
    if freeze.get("selected_transaction_bytes") != sum(int(item["size"]) for item in items):
        raise ValueError("freeze manifest byte total differs from frozen selection")
    records = freeze.get("transaction_objects")
    if not isinstance(records, list) or len(records) != len(items):
        raise ValueError("freeze manifest object count differs from frozen selection")
    return listing_bytes, items, freeze_bytes, freeze


def audit_object(item: dict, record: dict, cache_dir: Path) -> dict:
    identity = freezer.source.object_identity(item)
    if freezer.source.object_identity(record) != identity:
        raise RuntimeError(f"freeze identity mismatch: {item['key']}")
    path = freezer.source.cache_path(cache_dir, item).resolve()
    if Path(str(record.get("cache_path", ""))).resolve() != path:
        raise RuntimeError(f"freeze cache path mismatch: {item['key']}")
    if not path.is_file() or path.stat().st_size != int(item["size"]):
        raise RuntimeError(f"cached object size mismatch: {item['key']}")
    digest = record.get("local_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise RuntimeError(f"invalid frozen SHA-256: {item['key']}")

    parquet = pq.ParquetFile(path)
    if parquet.metadata.num_rows < 1 or parquet.metadata.num_row_groups < 1:
        raise RuntimeError(f"empty Parquet object: {item['key']}")
    schema = parquet.schema_arrow
    has_inputs = validate_schema(schema, str(item["key"]))
    missing_inputs_coinbase_only = False
    if not has_inputs:
        guard = parquet.read(columns=["is_coinbase", "input_count"]).to_pydict()
        if not all(guard["is_coinbase"]) or any(guard["input_count"]):
            raise RuntimeError(f"non-coinbase rows lack inputs: {item['key']}")
        missing_inputs_coinbase_only = True
    schema_text = str(schema.remove_metadata())
    return {
        **identity,
        "cache_identity": freezer.source.cache_identity(item),
        "local_sha256": digest,
        "rows": parquet.metadata.num_rows,
        "row_groups": parquet.metadata.num_row_groups,
        "schema_sha256": hashlib.sha256(schema_text.encode("utf-8")).hexdigest(),
        "top_level_columns": schema.names,
        "inputs_present": has_inputs,
        "missing_inputs_coinbase_only": missing_inputs_coinbase_only,
    }


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--listing")
    argument_parser.add_argument("--expected-listing-sha256", type=freezer.sha256_arg)
    argument_parser.add_argument("--freeze-manifest")
    argument_parser.add_argument("--cache-dir")
    argument_parser.add_argument("--output")
    argument_parser.add_argument("--self-test", action="store_true")
    return argument_parser


def self_test() -> None:
    outputs = pa.field(
        "outputs",
        pa.list_(
            pa.struct(
                [
                    pa.field("index", pa.int64()),
                    pa.field("script_hex", pa.string()),
                    pa.field("value", pa.float64()),
                ]
            )
        ),
    )
    inputs = pa.field(
        "inputs",
        pa.list_(
            pa.struct(
                [
                    pa.field("index", pa.int64()),
                    pa.field("spent_transaction_hash", pa.string()),
                    pa.field("spent_output_index", pa.int64()),
                    pa.field("value", pa.float64()),
                ]
            )
        ),
    )
    base = [
        pa.field("txid", pa.string()),
        pa.field("hash", pa.string()),
        pa.field("block_hash", pa.string()),
        pa.field("block_number", pa.int64()),
        pa.field("index", pa.int64()),
        pa.field("input_count", pa.int64()),
        pa.field("output_count", pa.int64()),
        pa.field("is_coinbase", pa.bool_()),
        outputs,
        pa.field("date", pa.string()),
    ]
    assert validate_schema(pa.schema(base + [inputs]), "full") is True
    assert validate_schema(pa.schema(base), "genesis") is False
    try:
        validate_schema(pa.schema(base[:-2] + [pa.field("date", pa.string())]), "bad")
    except RuntimeError as error:
        assert "outputs" in str(error)
    else:
        raise AssertionError("missing outputs must fail")


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"self_test": "passed", "effect_metrics_read": False}))
        return 0
    required = {
        "--listing": args.listing,
        "--expected-listing-sha256": args.expected_listing_sha256,
        "--freeze-manifest": args.freeze_manifest,
        "--cache-dir": args.cache_dir,
        "--output": args.output,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        raise ValueError(f"missing required arguments: {missing}")

    listing_path = Path(args.listing)
    freeze_path = Path(args.freeze_manifest)
    cache_dir = Path(args.cache_dir).resolve()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    freezer.source.preflight_output_parent(output)
    listing_bytes, items, freeze_bytes, freeze = load_inputs(
        listing_path, args.expected_listing_sha256, freeze_path
    )
    records_by_key = {record["key"]: record for record in freeze["transaction_objects"]}
    if len(records_by_key) != len(items):
        raise RuntimeError("freeze manifest contains duplicate object keys")

    started = dt.datetime.now(dt.timezone.utc).isoformat()
    records = []
    for index, item in enumerate(items, start=1):
        record = records_by_key.get(item["key"])
        if record is None:
            raise RuntimeError(f"freeze manifest lacks object: {item['key']}")
        records.append(audit_object(item, record, cache_dir))
        if index == 1 or index % 100 == 0 or index == len(items):
            print(f"audited schema {index}/{len(items)}: {item['key']}", file=sys.stderr)
    ended = dt.datetime.now(dt.timezone.utc).isoformat()
    schema_counts = Counter(record["schema_sha256"] for record in records)
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_transaction_schema_audit_complete",
        "candidate_scope": "aws_public_bitcoin_prefix_source_qualification_only",
        "listing_file": str(listing_path.resolve()),
        "listing_file_sha256": hashlib.sha256(listing_bytes).hexdigest(),
        "freeze_manifest": str(freeze_path.resolve()),
        "freeze_manifest_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "script_sha256": script_sha256(),
        "started_utc": started,
        "ended_utc": ended,
        "cache_dir": str(cache_dir),
        "transaction_objects": records,
        "object_count": len(records),
        "row_count": sum(record["rows"] for record in records),
        "schema_variant_counts": dict(sorted(schema_counts.items())),
        "missing_inputs_coinbase_only_objects": sum(
            record["missing_inputs_coinbase_only"] for record in records
        ),
        "metadata_and_coinbase_guard_columns_read": True,
        "full_transaction_rows_read": False,
        "effect_metrics_read": False,
        "formal_gate": False,
        "s0_authorized": False,
        "limitations": [
            "This artifact validates physical schemas and the coinbase-only "
            "missing-inputs exception.",
            "Transaction position uniqueness, prevout closure, integer-satoshi "
            "recovery and value conservation remain unaudited.",
        ],
    }
    freezer.source.atomic_write_new(output, freezer.source.canonical_json(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(output),
                "object_count": result["object_count"],
                "row_count": result["row_count"],
                "schema_variants": len(schema_counts),
                "effect_metrics_read": False,
                "s0_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
