#!/usr/bin/env python3
"""Bind S0 evaluation to its independent provenance audit without opening S1."""
import argparse
import hashlib
import json
import os
from pathlib import Path


PROTOCOL_VERSION = "Gate3A-v1.3-20260912"
PROVENANCE_STATUS = "integrity_component_complete"
FINAL_FAILURE_STATUS = "integrity_failed_repair_or_nogo_pending"


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _atomic_new(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError("refusing to overwrite output")
    temporary = path.with_name(path.name + ".tmp")
    try:
        with open(temporary, "xb") as handle:
            handle.write(payload)
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _load(path):
    with open(path, encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("input JSON must be an object")
    return value


def _need(record, key):
    if key not in record:
        raise ValueError(f"missing {key}")
    return record[key]


def _sha(value, name):
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"invalid {name}")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"invalid {name}") from error
    return value.lower()


def _validate_bindings(provenance, evaluation):
    if _need(evaluation, "protocol_version") != PROTOCOL_VERSION:
        raise ValueError("unexpected protocol_version")
    source = _sha(_need(provenance, "source_manifest_sha256"), "source_manifest_sha256")
    if source != _sha(_need(evaluation, "source_manifest_sha256"), "source_manifest_sha256"):
        raise ValueError("source manifest binding mismatch")
    summary = _sha(_need(provenance, "extraction_summary_sha256"), "extraction_summary_sha256")
    if summary != _sha(_need(evaluation, "extractor_summary_sha256"), "extractor_summary_sha256"):
        raise ValueError("extraction summary binding mismatch")
    inputs = _need(evaluation, "inputs")
    if not isinstance(inputs, dict):
        raise ValueError("evaluation inputs must be an object")
    if summary != _sha(_need(inputs, "summary_sha256"), "inputs.summary_sha256"):
        raise ValueError("evaluation summary binding mismatch")
    state = _sha(_need(provenance, "state_db_sha256"), "state_db_sha256")
    if state != _sha(_need(inputs, "state_db_sha256"), "inputs.state_db_sha256"):
        raise ValueError("state DB binding mismatch")
    return {"source_manifest_sha256": source, "extraction_summary_sha256": summary,
            "state_db_sha256": state,
            "union_log_sha256": _sha(_need(evaluation, "union_log_sha256"), "union_log_sha256")}


def _validate_provenance(provenance):
    if _need(provenance, "status") != PROVENANCE_STATUS:
        raise ValueError("unexpected provenance status")
    if _need(provenance, "state_quick_check") != "ok":
        raise ValueError("provenance state_quick_check is not ok")
    if any(_need(provenance, key) is not False for key in ("effect_metrics_read", "labels_read", "models_authorized")):
        raise ValueError("provenance violates label/model/effect boundary")
    target = _need(provenance, "sample_target")
    sampled = _need(provenance, "sampled_unique_events")
    recovered = _need(provenance, "fully_recovered")
    minimum = _need(provenance, "minimum_required")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (target, sampled, recovered, minimum)):
        raise ValueError("provenance sample counts must be non-bool integers")
    if (target, sampled, minimum) != (1000, 1000, 995) or not 0 <= recovered <= sampled:
        raise ValueError("provenance sample counts violate frozen threshold")
    threshold = recovered >= minimum
    if not isinstance(_need(provenance, "threshold_passed"), bool) or provenance["threshold_passed"] is not threshold:
        raise ValueError("provenance threshold_passed disagrees with recovered count")
    return threshold


def _validate_evaluation(evaluation):
    if _need(evaluation, "effect_metrics_read") is not True:
        raise ValueError("evaluation must read effect metrics")
    if any(_need(evaluation, key) is not False for key in ("labels_read", "models_authorized")):
        raise ValueError("evaluation violates label/model boundary")
    integrity = _need(evaluation, "integrity")
    decision = _need(evaluation, "decision")
    if not isinstance(integrity, dict) or not isinstance(decision, dict):
        raise ValueError("evaluation integrity and decision must be objects")
    if (integrity.get("status") != "pending_external_provenance_audit"
            or integrity.get("pending_external_provenance_audit") is not True
            or decision.get("status") != "pending" or decision.get("final_integrity") != "pending"):
        raise ValueError("evaluation is not awaiting final provenance")
    candidate = decision.get("candidate")
    if candidate not in {"Go", "No-Go", "Inconclusive"}:
        raise ValueError("invalid S0 candidate")
    return candidate


def finalize(provenance_path, evaluation_path, output):
    provenance_path, evaluation_path = Path(provenance_path), Path(evaluation_path)
    provenance, evaluation = _load(provenance_path), _load(evaluation_path)
    bindings = _validate_bindings(provenance, evaluation)
    candidate = _validate_evaluation(evaluation)
    passed = _validate_provenance(provenance)
    result = {
        "schema_version": "aws-btc-s0-final-decision-v1",
        "protocol_version": PROTOCOL_VERSION,
        "status": "finalized" if passed else FINAL_FAILURE_STATUS,
        "outcome": candidate if passed else None,
        "final_integrity": "passed" if passed else "failed",
        "s1_protocol_drafting_allowed": passed and candidate == "Go",
        "models_authorized": False,
        "effect_metrics_read": True,
        "labels_read": False,
        "bindings": bindings,
        "integrity": {key: provenance[key] for key in ("threshold_passed", "sample_target", "sampled_unique_events", "fully_recovered", "minimum_required")},
        "inputs": {
            "provenance": {"path": str(provenance_path.resolve()), "sha256": _sha256(provenance_path)},
            "evaluation": {"path": str(evaluation_path.resolve()), "sha256": _sha256(evaluation_path)},
        },
        "runner_sha256": _sha256(Path(__file__)),
        "limitations": [
            "S0 finalization does not authorize models or training.",
            "A Go only permits drafting a separately frozen S1 protocol.",
            "The experiment registry is not modified automatically.",
        ],
    }
    _atomic_new(output, (_canonical(result) + "\n").encode("ascii"))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--evaluation", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = finalize(args.provenance, args.evaluation, args.output)
    print(_canonical({"status": result["status"], "outcome": result["outcome"], "models_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
