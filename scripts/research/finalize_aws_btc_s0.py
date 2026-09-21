#!/usr/bin/env python3
"""Bind S0 evaluation to its independent provenance audit without opening S1."""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path


PROTOCOL_VERSION = "Gate3A-v1.3-20260912"
PROVENANCE_STATUS = "integrity_component_complete"
FINAL_FAILURE_STATUS = "integrity_failed_repair_or_nogo_pending"
ORIGINAL_PROVENANCE_SHA256 = "ff35f121ae3da16ccf2834f7f2d13b6c6aa1220cabf28ad58102e9a9e3aae4f0"
ORIGINAL_AUDITOR_SHA256 = "b72a05d60c59309af1f8431be4dfc02e3137820db0d7a97f3e3fbfa34a6b42f2"
CELLS = [f"t{cutoff}|{profile}" for cutoff in (181440, 199584, 215712, 225792)
         for profile in ("F_pub", "F_wide")]


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


def _validate_correction(provenance_path, checkpoint_path, correction_path, provenance):
    correction = _load(correction_path)
    if (_sha256(provenance_path) != ORIGINAL_PROVENANCE_SHA256
            or provenance.get("auditor_sha256") != ORIGINAL_AUDITOR_SHA256
            or provenance.get("assigned_cells") != {"window_id|cutoff|future|profile": 0}):
        raise ValueError("not the known assigned_cells defect")
    if (correction.get("schema_version") != "aws-btc-s0-provenance-correction-v1"
            or correction.get("scope") != "assigned_cells_only"
            or correction.get("provenance_sha256") != ORIGINAL_PROVENANCE_SHA256
            or correction.get("checkpoint_sha256") != _sha256(checkpoint_path)
            or correction.get("checkpoint_events_match") is not True):
        raise ValueError("correction binding mismatch")
    events = _need(provenance, "events")
    if not isinstance(events, list) or len(events) != 1000:
        raise ValueError("correction event count mismatch")
    groups = {cell: [] for cell in CELLS}
    event_by_id = {}
    for event in events:
        event_id = event["event_id"]
        if not isinstance(event_id, str) or len(event_id) != 64 or event_id != event_id.lower() or event_id in event_by_id:
            raise ValueError("invalid or duplicate correction event ID")
        try:
            rank = hashlib.sha256(bytes.fromhex(event_id) + b"asof-audit-v1").hexdigest()
        except ValueError as error:
            raise ValueError("invalid correction event ID") from error
        if event.get("rank") != rank or event.get("assigned_cell") not in groups or type(event.get("recovered")) is not bool:
            raise ValueError("invalid correction event")
        groups[event["assigned_cell"]].append(event)
        event_by_id[event_id] = event
    counts = {cell: len(groups[cell]) for cell in CELLS}
    if (min(counts.values()) < 100 or correction.get("corrected_assigned_cells") != counts
            or correction.get("sampled_unique_events") != len(events)
            or correction.get("fully_recovered") != sum(event["recovered"] for event in events)
            or correction["fully_recovered"] != provenance["fully_recovered"]):
        raise ValueError("corrected cell or recovery count mismatch")
    sorted_groups = [sorted(groups[cell], key=lambda event: (event["rank"], event["event_id"])) for cell in CELLS]
    ordered = [event for group in sorted_groups for event in group[:100]]
    ordered += [group[index] for index in range(100, max(map(len, sorted_groups))) for group in sorted_groups if index < len(group)]
    selection_hash = hashlib.sha256(_canonical([{"cell": event["assigned_cell"], "event_id": event["event_id"]} for event in ordered]).encode("ascii")).hexdigest()
    if correction.get("selection_sha256") != selection_hash:
        raise ValueError("corrected selection hash mismatch")
    with sqlite3.connect(checkpoint_path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as checkpoint:
        if checkpoint.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("checkpoint quick_check failed")
        bindings = json.loads(checkpoint.execute("SELECT value FROM metadata WHERE key='bindings'").fetchone()[0])
        if (hashlib.sha256(_canonical(bindings).encode("ascii")).hexdigest() != provenance["checkpoint_bindings_sha256"]
                or bindings.get("selection_sha256") != selection_hash
                or bindings.get("auditor_sha256") != ORIGINAL_AUDITOR_SHA256
                or bindings.get("state_db_sha256") != provenance["state_db_sha256"]
                or bindings.get("summary_sha256") != provenance["extraction_summary_sha256"]
                or bindings.get("source_manifest_sha256") != provenance["source_manifest_sha256"]):
            raise ValueError("checkpoint binding mismatch")
        checkpoint_events = list(checkpoint.execute("SELECT event_id,assigned_cell,ok,reason FROM events"))
        if len(checkpoint_events) != len(events):
            raise ValueError("checkpoint event count mismatch")
        for event_id, cell, ok, reason in checkpoint_events:
            event = event_by_id.get(event_id.hex())
            if event is None or (event["assigned_cell"], event["recovered"], event["reason"]) != (cell, bool(ok), reason):
                raise ValueError("checkpoint event mismatch")
        for key, field in (("parent_object_index", "parent_objects_verified_total"),
                           ("parent_rows_verified_total", "parent_rows_verified_total")):
            if json.loads(checkpoint.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()[0]) != provenance[field]:
                raise ValueError(f"checkpoint {key} mismatch")
    return counts


def finalize(provenance_path, evaluation_path, evaluation2_path, correction_path, checkpoint_path, output):
    provenance_path, evaluation_path, evaluation2_path = map(Path, (provenance_path, evaluation_path, evaluation2_path))
    correction_path, checkpoint_path = Path(correction_path), Path(checkpoint_path)
    if evaluation_path.resolve() == evaluation2_path.resolve() or _sha256(evaluation_path) != _sha256(evaluation2_path):
        raise ValueError("independent evaluations differ or reuse one path")
    provenance, evaluation = _load(provenance_path), _load(evaluation_path)
    bindings = _validate_bindings(provenance, evaluation)
    candidate = _validate_evaluation(evaluation)
    passed = _validate_provenance(provenance)
    corrected_cells = _validate_correction(provenance_path, checkpoint_path, correction_path, provenance)
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
        "integrity": {**{key: provenance[key] for key in ("threshold_passed", "sample_target", "sampled_unique_events", "fully_recovered", "minimum_required")},
                      "corrected_assigned_cells": corrected_cells, "correction_scope": "assigned_cells_only"},
        "inputs": {
            "provenance": {"path": str(provenance_path.resolve()), "sha256": _sha256(provenance_path)},
            "evaluation": {"path": str(evaluation_path.resolve()), "sha256": _sha256(evaluation_path)},
            "evaluation2": {"path": str(evaluation2_path.resolve()), "sha256": _sha256(evaluation2_path)},
            "correction": {"path": str(correction_path.resolve()), "sha256": _sha256(correction_path)},
            "checkpoint": {"path": str(checkpoint_path.resolve()), "sha256": _sha256(checkpoint_path)},
        },
        "runner_sha256": _sha256(Path(__file__)),
        "limitations": [
            "S0 finalization does not authorize models or training.",
            "A Go only permits drafting a separately frozen S1 protocol.",
            "The experiment registry is not modified automatically.",
            "Original provenance assigned_cells is defective; the bound correction repairs only that summary field.",
            "The correction does not re-scan source transactions or independently recompute candidate selection.",
        ],
    }
    _atomic_new(output, (_canonical(result) + "\n").encode("ascii"))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--evaluation", required=True)
    parser.add_argument("--evaluation2", required=True)
    parser.add_argument("--correction", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = finalize(args.provenance, args.evaluation, args.evaluation2, args.correction, args.checkpoint, args.output)
    print(_canonical({"status": result["status"], "outcome": result["outcome"], "models_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
