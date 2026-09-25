#!/usr/bin/env python3
"""Acceptance verification for the frozen AWS prefix after transfer to the lab server.

Two questions are answered separately:

  correct  — are the server bytes the same bytes as the frozen local copy?
             transactions are checked object by object against the manifest-bound
             local_sha256 recorded in the transaction byte freeze; blocks, sidecars
             and the semantic state DB against sha256 manifests computed on the
             source host; the S0 state DB against its frozen full-file hash.

  usable   — can the transferred artifacts actually be consumed? The S0 state DB
             must pass SQLite quick_check and its table row counts must equal the
             frozen extractor summary counters; sampled parquet objects must open
             under pyarrow. Byte identity implies this, but a direct check is cheap
             and catches a silently truncated or mis-placed file.
"""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path("/workspace/chenquan/asof-entity-graph")
DATA = ROOT / "data/raw/aws_btc_prefix_v0_1_20260910"
FREEZE = ROOT / "experiments/diagnostics/aws_btc_transaction_byte_freeze_v0_1_20260910.json"
SUMMARY = ROOT / "experiments/diagnostics/aws_btc_s0_union_extract_v1_1_20260911/summary.json"
BLOCKS_MANIFEST = Path("/workspace/chenquan/blocks_local_sha256.txt")
SIDECAR_MANIFEST = Path("/workspace/chenquan/tx_sidecar_local_sha256.txt")
UTXO_EXPECTED = "6cafc290b8e3b951417c85c5b6dd431e71c3d0c548ac45bdc6a7bdee4a34d924"
S0_DB_EXPECTED = "1f1bf354519af4dcc1e0cc3ae3da0c670d057bd5897db6bf806e3442bc078205"
S0_DB_NAME = "s0_state/s0_union_v1_1.sqlite"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_manifest(manifest, directory, label):
    missing, mismatched, ok = [], [], 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split("  ", 1)
        path = directory / name
        if not path.exists():
            missing.append(name)
            continue
        if sha256(path) == expected:
            ok += 1
        else:
            mismatched.append(name)
    print(json.dumps({"check": label, "ok": ok, "missing": len(missing),
                      "mismatched": len(mismatched),
                      "missing_sample": missing[:5], "mismatched_sample": mismatched[:5]}),
          flush=True)
    return ok, missing, mismatched


def check_transactions():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    objects = freeze["transaction_objects"]
    tx_dir = DATA / "transactions"
    ok = missing = bad = size_bad = 0
    bad_sample = []
    for obj in objects:
        path = tx_dir / (obj["cache_identity"] + ".parquet")
        if not path.exists():
            missing += 1
            continue
        if path.stat().st_size != obj["size"]:
            size_bad += 1
            continue
        if sha256(path) == obj["local_sha256"]:
            ok += 1
        else:
            bad += 1
            if len(bad_sample) < 5:
                bad_sample.append(obj["cache_identity"])
    print(json.dumps({"check": "correct::transactions_vs_byte_freeze", "expected": len(objects),
                      "ok": ok, "missing": missing, "hash_mismatch": bad,
                      "size_mismatch": size_bad, "hash_mismatch_sample": bad_sample}), flush=True)
    return ok == len(objects)


def check_state_db():
    """Usability of the S0 state DB: hash, quick_check and counters against the summary."""
    db = DATA / S0_DB_NAME
    if not db.exists():
        print(json.dumps({"check": "usable::state_db", "status": "missing"}))
        return False
    got = sha256(db)
    print(json.dumps({"check": "correct::state_db_hash", "expected": S0_DB_EXPECTED, "got": got,
                      "match": got == S0_DB_EXPECTED}), flush=True)
    if got != S0_DB_EXPECTED:
        return False

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    uri = f"file:{db.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        print(json.dumps({"check": "usable::quick_check", "result": quick}), flush=True)
        if quick != "ok":
            return False
        metadata = {key: json.loads(value)
                    for key, value in connection.execute("SELECT key,value FROM metadata")}
        counters = summary["s0_counters"]
        rows = {}
        for table in ("union_events", "window_transactions", "window_support"):
            rows[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        expected = {table: counters[table] for table in rows}
        height_ok = metadata.get("last_committed_height") == summary["last_complete_height"]
        print(json.dumps({"check": "usable::counters", "rows": rows, "expected": expected,
                          "match": rows == expected,
                          "last_committed_height": metadata.get("last_committed_height"),
                          "height_match": height_ok}), flush=True)
        return rows == expected and height_ok
    finally:
        connection.close()


def check_parquet_samples(count=5):
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        print(json.dumps({"check": "usable::parquet", "status": "pyarrow unavailable",
                          "detail": str(error)}))
        return False
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    objects = sorted(freeze["transaction_objects"], key=lambda o: -o["size"])
    sample = objects[:count] if len(objects) > count else objects
    ok = 0
    for obj in sample:
        path = DATA / "transactions" / (obj["cache_identity"] + ".parquet")
        try:
            parquet = pq.ParquetFile(path)
            meta = parquet.metadata
            ok += 1
            print(json.dumps({"check": "usable::parquet_open", "file": obj["cache_identity"],
                              "rows": meta.num_rows, "row_groups": meta.num_row_groups,
                              "columns": len(parquet.schema_arrow)}), flush=True)
        except Exception as error:  # noqa: BLE001
            print(json.dumps({"check": "usable::parquet_open", "file": obj["cache_identity"],
                              "error": str(error)[:160]}), flush=True)
    print(json.dumps({"check": "usable::parquet_summary", "opened": ok, "sampled": len(sample)}))
    return ok == len(sample)


def main():
    failures = []
    if not check_transactions():
        failures.append("transactions")
    b_ok, b_missing, b_bad = check_manifest(BLOCKS_MANIFEST, DATA / "blocks",
                                            "correct::blocks_vs_local_manifest")
    if b_missing or b_bad:
        failures.append("blocks")
    s_ok, s_missing, s_bad = check_manifest(SIDECAR_MANIFEST, DATA / "transactions",
                                            "correct::tx_sidecars_vs_local_manifest")
    if s_missing or s_bad:
        failures.append("tx_sidecars")
    utxo = DATA / "semantic_state/utxo_v0_2.sqlite"
    if not utxo.exists():
        print(json.dumps({"check": "correct::semantic_state", "status": "missing"}))
        failures.append("semantic_state")
    else:
        got = sha256(utxo)
        print(json.dumps({"check": "correct::semantic_state", "expected": UTXO_EXPECTED,
                          "got": got, "match": got == UTXO_EXPECTED}), flush=True)
        if got != UTXO_EXPECTED:
            failures.append("semantic_state")
    if not check_state_db():
        failures.append("state_db")
    if not check_parquet_samples():
        failures.append("parquet_readability")

    print(json.dumps({"acceptance": "PASS" if not failures else "FAIL",
                      "failed_checks": failures}))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
