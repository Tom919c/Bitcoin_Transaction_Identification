from __future__ import annotations

import subprocess
import sys
import sqlite3
import random
import hashlib
from argparse import Namespace
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import audit_aws_btc_s0_provenance as audit  # noqa: E402
import extract_aws_btc_s0_events as extract  # noqa: E402


def test_self_test() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/research/audit_aws_btc_s0_provenance.py"), "--self-test"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"self_test": "passed"' in result.stdout


def test_ro_connect_enforces_query_only_on_file_database(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite"
    writer = sqlite3.connect(path); writer.execute("CREATE TABLE probe(value INTEGER)"); writer.commit(); writer.close()
    connection = audit.ro_connect(path)
    assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
    with pytest.raises(sqlite3.OperationalError):
        connection.execute("INSERT INTO probe VALUES(1)")
    connection.close()


def test_digest_streams_large_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "large.bin"
    path.write_bytes(b"x" * (9 * 1024 * 1024) + b"y")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(Path, "read_bytes", lambda self: (_ for _ in ()).throw(AssertionError("not streaming")))
    assert audit.digest(path) == expected


def test_load_summary_rejects_self_consistent_nonprotocol_design(tmp_path: Path) -> None:
    summary = {"status": "s0_union_extraction_complete", "s0_extraction_complete": True, "source_manifest_sha256": audit.FROZEN_MANIFEST_SHA256, "runner_sha256": "r", "design": audit.FROZEN_DESIGN, "s0_counters": {"union_events": 1}, "transaction_counters": {"blocks": audit.FROZEN_LAST_HEIGHT + 1}, "horizon_cells": extract.horizon_cells(audit.FROZEN_DESIGN, 290291), "windows": extract.build_windows(audit.FROZEN_DESIGN), "target_height": audit.FROZEN_TARGET_HEIGHT, "last_complete_height": audit.FROZEN_LAST_HEIGHT, "effect_metrics_read": False, "labels_read": False}
    path = tmp_path / "summary.json"; path.write_bytes(audit.canonical(summary))
    assert audit.load_summary(path)["target_height"] == audit.FROZEN_TARGET_HEIGHT
    summary["target_height"] = 1; path.write_bytes(audit.canonical(summary))
    with pytest.raises(ValueError, match="frozen S0 target"):
        audit.load_summary(path)


def _naive_candidates(connection: sqlite3.Connection, summary: dict) -> dict[tuple[str, str], list[sqlite3.Row]]:
    connection.row_factory = sqlite3.Row
    result: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for cell in audit.cells(summary):
        dsu = audit.DSU()
        excluded = "exclude_f_pub" if cell["profile"] == "F_pub" else "exclude_f_wide"
        for row in connection.execute(
            f"SELECT script_id_a,script_id_b FROM union_events WHERE height<=? AND {excluded}=0 ORDER BY height,tx_index,event_index,script_id_a,script_id_b",
            (cell["future"],),
        ):
            dsu.union(row[0], row[1])
        roots = {dsu.find(row[0]) for row in connection.execute("SELECT script_id FROM window_support WHERE window_id=?", (cell["window_id"],))}
        heap: list[tuple[bytes, bytes, sqlite3.Row]] = []
        for row in connection.execute(
            f"SELECT * FROM union_events WHERE height<=? AND {excluded}=0 ORDER BY height,tx_index,event_index,script_id_a,script_id_b",
            (cell["future"],),
        ):
            if dsu.find(row["script_id_a"]) not in roots and dsu.find(row["script_id_b"]) not in roots:
                continue
            rank, event_id = audit.event_rank(row["event_id"])
            item = (audit.reverse_bytes(rank), audit.reverse_bytes(event_id), row)
            if len(heap) < audit.SAMPLE_TARGET:
                audit.heapq.heappush(heap, item)
            elif item[:2] > heap[0][:2]:
                audit.heapq.heapreplace(heap, item)
        result[cell["window_id"], cell["profile"]] = sorted((item[2] for item in heap), key=lambda row: audit.event_rank(row["event_id"]))
    return result


def test_incremental_candidates_match_naive_with_future_connectors_and_global_allocation() -> None:
    state = sqlite3.connect(":memory:")
    state.row_factory = sqlite3.Row
    extract.create_s0_schema(state)
    design = {"cutoff_heights": [2, 4, 6, 8], "primary_horizon_blocks": 2, "profiles": ["F_pub", "F_wide"]}
    for cutoff in design["cutoff_heights"]:
        state.execute("INSERT INTO window_support VALUES(?,?,?)", (f"t{cutoff}", b"a" * 32, cutoff))
    rng = random.Random(20260912)
    scripts = [b"a" * 32] + [number.to_bytes(32, "big") for number in range(1, 17)]
    pairs = [(scripts[index], scripts[index + 1]) for index in range(len(scripts) - 1)]
    pairs.extend((rng.choice(scripts), rng.choice(scripts)) for _ in range(1_300))
    for number, (left, right) in enumerate(pairs):
        event_id = number.to_bytes(32, "big")
        height = 1 if number == 0 else 4 if number == 1 else rng.randrange(11)
        state.execute(
            "INSERT INTO union_events VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, b"h" * 32, height, number.to_bytes(32, "big"), number, 0, left, right, number % 17 == 0, number % 11 == 0, "{}"),
        )
    summary = {"design": design}
    naive = _naive_candidates(state, summary)
    instrumentation: dict[str, int] = {}
    incremental = audit.candidates(state, summary, instrumentation)
    assert list(incremental) == [(cell["window_id"], cell["profile"]) for cell in audit.cells(summary)]
    assert {cell: [row["event_id"] for row in values] for cell, values in incremental.items()} == {cell: [row["event_id"] for row in values] for cell, values in naive.items()}
    assert instrumentation["F_pub_dsu_cursors"] == instrumentation["F_wide_dsu_cursors"] == 1
    assert [(cell, row["event_id"]) for cell, row in audit.allocate(incremental)] == [(cell, row["event_id"]) for cell, row in audit.allocate(naive)]


def _hex(value: int) -> str:
    return f"{value:064x}"


def _row(txid: int, height: int, index: int, inputs: list[dict], outputs: list[dict]) -> dict:
    return {
        "txid": _hex(txid), "hash": _hex(txid), "block_hash": _hex(99 + height),
        "block_number": height, "index": index, "input_count": len(inputs),
        "output_count": len(outputs), "is_coinbase": not inputs,
        "input_value": None if not inputs else sum(item["value"] for item in inputs),
        "output_value": sum(item["value"] for item in outputs),
        "fee": None if not inputs else sum(item["value"] for item in inputs) - sum(item["value"] for item in outputs),
        "inputs": inputs, "outputs": outputs, "date": "2009-01-03",
    }


def _scan_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, child_twice=False, bad_source=False, duplicate_parent=False, bip30_version=False, bad_value=False):
    parent_key = "v1.0/btc/transactions/date=2009-01-03/parents.parquet"
    source_key = "v1.0/btc/transactions/date=2009-01-03/source.parquet"
    parent = _row(1, 0, 0, [], [{"index": 0, "script_hex": "51", "value": 50.0}, {"index": 1, "script_hex": "52", "value": 50.0}])
    replacement = _row(1, 1, 0, [], [{"index": 0, "script_hex": "51", "value": 50.0}, {"index": 1, "script_hex": "52", "value": 50.0}])
    inputs = [
        {"index": 0, "spent_transaction_hash": _hex(1), "spent_output_index": 0, "value": 49.0 if bad_value else 50.0},
        {"index": 1, "spent_transaction_hash": _hex(1), "spent_output_index": 1, "value": 50.0},
    ]
    child = _row(3, 2 if bip30_version else 1, 0, inputs, [{"index": 0, "script_hex": "53", "value": 100.0 if not bad_value else 99.0}])
    parent_rows = [parent, parent] if duplicate_parent else [parent]
    if bip30_version: parent_rows.append(replacement)
    source_rows = [child] + ([child] if child_twice else [])
    parent_path = tmp_path / "parents.parquet"; pq.write_table(pa.Table.from_pylist(parent_rows), parent_path)
    source_path = tmp_path / "source.parquet"; pq.write_table(pa.Table.from_pylist(source_rows), source_path)
    scripts = [extract.raw_script_id_bytes(bytes.fromhex("51"), "a"), extract.raw_script_id_bytes(bytes.fromhex("52"), "b")]
    height = 2 if bip30_version else 1
    facts = extract.transaction_profile_facts({"inputs": [{"index": 0, "value_sat": 5_000_000_000}, {"index": 1, "value_sat": 5_000_000_000}], "outputs": [{"index": 0, "script": bytes.fromhex("53"), "value_sat": 10_000_000_000}], "source": f"{source_key} height={height} index=0"}, scripts)
    anchor, member, member_indices = facts["triples"][0]
    block_hash = bytes.fromhex(_hex(99 + height)); txid = bytes.fromhex(_hex(3)); manifest = "a" * 64
    event_id = extract.compute_event_id(manifest, block_hash, height, txid, 0, 0, anchor, member, extract.HEURISTIC_VERSION)
    source = f"{source_key} height={height} index=0" + (" tampered" if bad_source else "")
    evidence = {"heuristic_id": "common-input", "source": source, "anchor_input_indices": [i for i, value in enumerate(scripts) if value == anchor], "member_input_indices": member_indices, "f_pub_matches": list(facts["f_pub_matches"]), "d_wp100k_matches": list(facts["d_wp100k_matches"]), "d_tx0_paper": bool(facts["d_tx0_paper"])}
    state = __import__("sqlite3").connect(":memory:"); state.row_factory = __import__("sqlite3").Row; extract.create_s0_schema(state)
    state.execute("INSERT INTO union_events VALUES(?,?,?,?,?,?,?,?,?,?,?)", (event_id, block_hash, height, txid, 0, 0, anchor, member, 0, 0, audit.canonical(evidence).decode()))
    event = state.execute("SELECT * FROM union_events").fetchone()
    checkpoint = audit.open_checkpoint(tmp_path / "checkpoint.sqlite", {"fixture": 1})
    opened: list[str] = []
    paths = {parent_key: parent_path, source_key: source_path}
    def cache_path(_cache: Path, item: dict) -> Path:
        opened.append(str(item["key"])); return paths[str(item["key"])]
    monkeypatch.setattr(audit.freezer.source, "cache_path", cache_path)
    return state, checkpoint, [(('t1', 'F_pub'), event)], [{"key": parent_key}, {"key": source_key}], {parent_key: {"rows": len(parent_rows), "inputs_present": False}, source_key: {"rows": len(source_rows), "inputs_present": True}}, manifest, opened


def test_stage_scan_normal_and_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state, checkpoint, selection, items, schema, manifest, opened = _scan_fixture(tmp_path, monkeypatch)
    first, counts = audit.scan_and_recompute(state, selection, items, schema, tmp_path, checkpoint, manifest)
    assert first[selection[0][1]["event_id"]] == (True, "recovered") and counts["parent_outputs"] == 2 and counts["matched_transactions"] == 1
    assert opened == [source_key := "v1.0/btc/transactions/date=2009-01-03/source.parquet", "v1.0/btc/transactions/date=2009-01-03/parents.parquet", source_key]
    opened.clear()
    second, resumed = audit.scan_and_recompute(state, selection, items, schema, tmp_path, checkpoint, manifest)
    assert second[selection[0][1]["event_id"]] == (True, "recovered") and resumed["parent_objects"] == 0 and opened == [source_key]


@pytest.mark.parametrize("kwargs, message", [
    ({"bad_source": True}, "source event did not locate exactly one"),
    ({"child_twice": True}, "source event did not locate exactly one"),
    ({"duplicate_parent": True}, "duplicate parent output version"),
])
def test_stage_scan_rejects_source_and_parent_tamper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kwargs: dict, message: str) -> None:
    state, checkpoint, selection, items, schema, manifest, _ = _scan_fixture(tmp_path, monkeypatch, **kwargs)
    with pytest.raises(RuntimeError, match=message):
        audit.scan_and_recompute(state, selection, items, schema, tmp_path, checkpoint, manifest)


def test_stage_scan_marks_value_mismatch_and_threshold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state, checkpoint, selection, items, schema, manifest, _ = _scan_fixture(tmp_path, monkeypatch, bad_value=True)
    result, _ = audit.scan_and_recompute(state, selection, items, schema, tmp_path, checkpoint, manifest)
    assert result[selection[0][1]["event_id"]] == (False, "parent_value_mismatch")
    assert not audit.integrity_passed(994)
    assert audit.integrity_passed(995)


def test_stage_scan_accepts_unique_bip30_parent_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state, checkpoint, selection, items, schema, manifest, _ = _scan_fixture(tmp_path, monkeypatch, bip30_version=True)
    result, counts = audit.scan_and_recompute(state, selection, items, schema, tmp_path, checkpoint, manifest)
    assert result[selection[0][1]["event_id"]] == (True, "recovered") and counts["parent_outputs"] == 4


def test_checkpoint_rejects_binding_tamper(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.sqlite"
    audit.open_checkpoint(path, {"summary_sha256": "a"}).close()
    with pytest.raises(RuntimeError, match="checkpoint bindings differ"):
        audit.open_checkpoint(path, {"summary_sha256": "b"})


def test_completed_resume_revalidates_frozen_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary_path = tmp_path / "summary.json"; summary_path.write_text("{}", encoding="utf-8")
    state_path = tmp_path / "state.sqlite"; sqlite3.connect(state_path).close()
    output = tmp_path / "audit.json"; checkpoint_path = tmp_path / "checkpoint.sqlite"
    event = {"event_id": b"e" * 32, "block_hash": b"b" * 32, "height": 1, "txid": b"t" * 32, "tx_index": 0, "event_index": 0, "script_id_a": b"a" * 32, "script_id_b": b"c" * 32}
    summary = {"design": audit.FROZEN_DESIGN}
    calls = {"frozen": 0}
    monkeypatch.setattr(audit, "parser", lambda: type("Parser", (), {"parse_args": lambda _: Namespace(completed_extraction_summary=str(summary_path), s0_state_db=str(state_path), transaction_cache_dir=str(tmp_path), output=str(output), temporary_state_db=str(checkpoint_path), self_test=False)})())
    monkeypatch.setattr(audit, "load_summary", lambda _: summary)
    monkeypatch.setattr(audit, "ro_connect", lambda _: sqlite3.connect(":memory:"))
    monkeypatch.setattr(audit, "state_bindings", lambda _connection, _summary: {"source_manifest_sha256": audit.FROZEN_MANIFEST_SHA256, "runner_sha256": "r", "union_events": 1})
    monkeypatch.setattr(audit, "candidates", lambda _connection, _summary: {})
    monkeypatch.setattr(audit, "allocate", lambda _candidates: [(('t181440', 'F_pub'), event)])
    monkeypatch.setattr(audit, "frozen_inputs", lambda *_: (calls.__setitem__("frozen", calls["frozen"] + 1) or ([], {})))
    original = audit.open_checkpoint
    def completed(path: Path, bindings: dict):
        connection = original(path, bindings)
        connection.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)", (event["event_id"], "t181440|F_pub", 1, "recovered"))
        connection.execute("INSERT OR REPLACE INTO metadata VALUES('parent_object_index','0')")
        connection.execute("INSERT OR REPLACE INTO metadata VALUES('parent_rows_verified_total','0')")
        connection.commit()
        return connection
    monkeypatch.setattr(audit, "open_checkpoint", completed)
    assert audit.main() == 0
    assert calls["frozen"] == 1
    result = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert result["parent_objects_verified_total"] == 0 and result["scan_counts_this_run"]["parent_objects"] == 0
    assert result["assigned_cells"]["t181440|F_pub"] == 1
    assert len(result["assigned_cells"]) == 8
