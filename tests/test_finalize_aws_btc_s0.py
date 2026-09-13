import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("finalize_s0", ROOT / "scripts/research/finalize_aws_btc_s0.py")
finalize_s0 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finalize_s0)


def _records(candidate="Go", recovered=1000):
    source, summary, state = "a" * 64, "b" * 64, "c" * 64
    provenance = {"status": "integrity_component_complete", "source_manifest_sha256": source,
                  "extraction_summary_sha256": summary, "state_db_sha256": state,
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


def _write(tmp_path, provenance, evaluation):
    p, e, out = tmp_path / "provenance.json", tmp_path / "evaluation.json", tmp_path / "final.json"
    p.write_text(json.dumps(provenance), encoding="utf-8")
    e.write_text(json.dumps(evaluation), encoding="utf-8")
    return p, e, out


def test_go_only_allows_s1_draft_not_models(tmp_path):
    p, e, out = _write(tmp_path, *_records())
    result = finalize_s0.finalize(p, e, out)
    assert result["outcome"] == "Go" and result["final_integrity"] == "passed"
    assert result["s1_protocol_drafting_allowed"] is True and result["models_authorized"] is False


def test_hash_binding_mismatch_is_rejected(tmp_path):
    provenance, evaluation = _records()
    evaluation["inputs"]["state_db_sha256"] = "d" * 64
    p, e, out = _write(tmp_path, provenance, evaluation)
    with pytest.raises(ValueError, match="state DB binding mismatch"):
        finalize_s0.finalize(p, e, out)
    assert not out.exists()


def test_failed_provenance_never_consumes_candidate(tmp_path):
    p, e, out = _write(tmp_path, *_records(recovered=994))
    result = finalize_s0.finalize(p, e, out)
    assert result["status"] == finalize_s0.FINAL_FAILURE_STATUS
    assert result["outcome"] is None and result["s1_protocol_drafting_allowed"] is False


def test_inconsistent_provenance_threshold_is_rejected(tmp_path):
    provenance, evaluation = _records(recovered=994)
    provenance["threshold_passed"] = True
    p, e, out = _write(tmp_path, provenance, evaluation)
    with pytest.raises(ValueError, match="threshold_passed"):
        finalize_s0.finalize(p, e, out)
    assert not out.exists()


def test_refuses_to_overwrite_output(tmp_path):
    p, e, out = _write(tmp_path, *_records(candidate="No-Go"))
    finalize_s0.finalize(p, e, out)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        finalize_s0.finalize(p, e, out)
