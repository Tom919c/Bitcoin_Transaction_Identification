import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


finalize_s0 = _module("finalize_s0", "scripts/research/finalize_aws_btc_s0.py")
correct_s0 = _module("correct_s0", "scripts/research/correct_aws_btc_s0_provenance.py")


def _records(candidate="Go", recovered=1000):
    source, summary, state = "a" * 64, "b" * 64, "c" * 64
    events = []
    for index in range(1000):
        event_id = index.to_bytes(32, "big")
        events.append({"event_id": event_id.hex(),
                       "rank": hashlib.sha256(event_id + b"asof-audit-v1").hexdigest(),
                       "assigned_cell": finalize_s0.CELLS[index // 125],
                       "recovered": index < recovered,
                       "reason": "recovered" if index < recovered else "parent_missing"})
    provenance = {"status": "integrity_component_complete", "source_manifest_sha256": source,
                  "extraction_summary_sha256": summary, "state_db_sha256": state,
                  "auditor_sha256": correct_s0.AUDITOR_SHA256,
                  "assigned_cells": {"window_id|cutoff|future|profile": 0},
                  "events": events, "parent_objects_verified_total": 10,
                  "parent_rows_verified_total": 20,
                  "state_quick_check": "ok", "sample_target": 1000, "sampled_unique_events": 1000,
                  "fully_recovered": recovered, "minimum_required": 995,
                  "threshold_passed": recovered >= 995, "effect_metrics_read": False,
                  "labels_read": False, "models_authorized": False}
    evaluation = {"protocol_version": finalize_s0.PROTOCOL_VERSION, "source_manifest_sha256": source,
                  "extractor_summary_sha256": summary, "inputs": {"summary_sha256": summary, "state_db_sha256": state},
                  "union_log_sha256": "d" * 64,
                  "effect_metrics_read": True, "labels_read": False, "models_authorized": False,
                  "integrity": {"status": "pending_external_provenance_audit", "pending_external_provenance_audit": True},
                  "decision": {"status": "pending", "candidate": candidate, "final_integrity": "pending"}}
    return provenance, evaluation


def _write(tmp_path, monkeypatch, provenance, evaluation):
    p, e1, e2 = (tmp_path / name for name in ("provenance.json", "evaluation1.json", "evaluation2.json"))
    checkpoint, correction, output = (tmp_path / name for name in ("checkpoint.sqlite", "correction.json", "final.json"))
    groups = {cell: sorted((event for event in provenance["events"] if event["assigned_cell"] == cell),
                           key=lambda event: (event["rank"], event["event_id"])) for cell in finalize_s0.CELLS}
    ordered = [event for cell in finalize_s0.CELLS for event in groups[cell][:100]]
    ordered += [groups[cell][index] for index in range(100, 125) for cell in finalize_s0.CELLS]
    selection = hashlib.sha256(correct_s0.canonical([{"cell": event["assigned_cell"], "event_id": event["event_id"]} for event in ordered])).hexdigest()
    bindings = {"source_manifest_sha256": provenance["source_manifest_sha256"],
                "summary_sha256": provenance["extraction_summary_sha256"],
                "state_db_sha256": provenance["state_db_sha256"],
                "auditor_sha256": provenance["auditor_sha256"], "selection_sha256": selection}
    provenance["checkpoint_bindings_sha256"] = hashlib.sha256(correct_s0.canonical(bindings)).hexdigest()
    with sqlite3.connect(checkpoint) as conn:
        conn.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)")
        conn.execute("CREATE TABLE events(event_id BLOB PRIMARY KEY,assigned_cell TEXT,ok INTEGER,reason TEXT)")
        conn.executemany("INSERT INTO metadata VALUES(?,?)", [
            ("bindings", json.dumps(bindings)), ("parent_object_index", "10"),
            ("parent_rows_verified_total", "20")])
        conn.executemany("INSERT INTO events VALUES(?,?,?,?)", [
            (bytes.fromhex(event["event_id"]), event["assigned_cell"], int(event["recovered"]), event["reason"])
            for event in provenance["events"]])
    p.write_text(json.dumps(provenance), encoding="utf-8")
    e1.write_text(json.dumps(evaluation), encoding="utf-8")
    e2.write_text(json.dumps(evaluation), encoding="utf-8")
    monkeypatch.setattr(correct_s0, "ORIGINAL_SHA256", correct_s0.sha256(p))
    monkeypatch.setattr(finalize_s0, "ORIGINAL_PROVENANCE_SHA256", correct_s0.sha256(p))
    correct_s0.correct(p, checkpoint, correction)
    return p, e1, e2, correction, checkpoint, output


def test_go_only_allows_s1_draft_not_models(tmp_path, monkeypatch):
    paths = _write(tmp_path, monkeypatch, *_records())
    result = finalize_s0.finalize(*paths)
    assert result["outcome"] == "Go" and result["final_integrity"] == "passed"
    assert result["s1_protocol_drafting_allowed"] is True and result["models_authorized"] is False
    assert result["integrity"]["corrected_assigned_cells"] == {cell: 125 for cell in finalize_s0.CELLS}
    assert result["inputs"]["correction"]["sha256"] == correct_s0.sha256(paths[3])


def test_rejects_tampered_correction_and_evaluation(tmp_path, monkeypatch):
    paths = _write(tmp_path, monkeypatch, *_records())
    correction = json.loads(paths[3].read_text())
    correction["corrected_assigned_cells"][finalize_s0.CELLS[0]] = 0
    paths[3].write_text(json.dumps(correction), encoding="utf-8")
    with pytest.raises(ValueError, match="corrected cell"):
        finalize_s0.finalize(*paths)
    assert not paths[-1].exists()
    correction["corrected_assigned_cells"][finalize_s0.CELLS[0]] = 125
    paths[3].write_text(json.dumps(correction), encoding="utf-8")
    paths[2].write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="independent evaluations differ"):
        finalize_s0.finalize(*paths)


def test_failed_provenance_never_consumes_candidate(tmp_path, monkeypatch):
    paths = _write(tmp_path, monkeypatch, *_records(recovered=994))
    result = finalize_s0.finalize(*paths)
    assert result["status"] == finalize_s0.FINAL_FAILURE_STATUS
    assert result["outcome"] is None and result["s1_protocol_drafting_allowed"] is False


def test_hash_binding_mismatch_is_rejected(tmp_path, monkeypatch):
    provenance, evaluation = _records()
    evaluation["inputs"]["state_db_sha256"] = "d" * 64
    paths = _write(tmp_path, monkeypatch, provenance, evaluation)
    with pytest.raises(ValueError, match="state DB binding mismatch"):
        finalize_s0.finalize(*paths)
    assert not paths[-1].exists()


def test_refuses_to_overwrite_output(tmp_path, monkeypatch):
    paths = _write(tmp_path, monkeypatch, *_records(candidate="No-Go"))
    finalize_s0.finalize(*paths)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        finalize_s0.finalize(*paths)
