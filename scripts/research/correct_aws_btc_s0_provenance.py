#!/usr/bin/env python3
"""Issue an immutable correction for the v1.3 S0 assigned_cells summary bug."""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path


ORIGINAL_SHA256 = "ff35f121ae3da16ccf2834f7f2d13b6c6aa1220cabf28ad58102e9a9e3aae4f0"
AUDITOR_SHA256 = "b72a05d60c59309af1f8431be4dfc02e3137820db0d7a97f3e3fbfa34a6b42f2"
CELLS = [f"t{cutoff}|{profile}" for cutoff in (181440, 199584, 215712, 225792)
         for profile in ("F_pub", "F_wide")]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def correct(provenance_path, checkpoint_path, output):
    provenance_path, checkpoint_path, output = map(Path, (provenance_path, checkpoint_path, output))
    if output.exists():
        raise FileExistsError("refusing to overwrite correction")
    if sha256(provenance_path) != ORIGINAL_SHA256:
        raise ValueError("unexpected original provenance hash")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("auditor_sha256") != AUDITOR_SHA256 or provenance.get("assigned_cells") != {"window_id|cutoff|future|profile": 0}:
        raise ValueError("correction applies only to the known summary bug")
    events = provenance["events"]
    if len(events) != provenance.get("sampled_unique_events") or len(events) != 1000:
        raise ValueError("event count mismatch")
    groups = {cell: [] for cell in CELLS}
    by_id = {}
    for event in events:
        event_id = event["event_id"]
        if len(event_id) != 64 or event_id != event_id.lower() or event_id in by_id:
            raise ValueError("invalid or duplicate event ID")
        raw_id = bytes.fromhex(event_id)
        if event["rank"] != hashlib.sha256(raw_id + b"asof-audit-v1").hexdigest():
            raise ValueError("event rank mismatch")
        if event["assigned_cell"] not in groups or type(event["recovered"]) is not bool:
            raise ValueError("invalid event assignment or recovery")
        groups[event["assigned_cell"]].append(event)
        by_id[event_id] = event
    if any(len(group) < 100 for group in groups.values()):
        raise ValueError("cell quota failed")
    if sum(event["recovered"] for event in events) != provenance["fully_recovered"]:
        raise ValueError("recovery count mismatch")
    ordered_groups = [sorted(groups[cell], key=lambda event: (event["rank"], event["event_id"])) for cell in CELLS]
    ordered = [event for group in ordered_groups for event in group[:100]]
    ordered += [group[index] for index in range(100, max(map(len, ordered_groups))) for group in ordered_groups if index < len(group)]
    selection_sha256 = hashlib.sha256(canonical([{"cell": event["assigned_cell"], "event_id": event["event_id"]} for event in ordered])).hexdigest()
    with sqlite3.connect(checkpoint_path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as checkpoint:
        if checkpoint.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("checkpoint quick_check failed")
        bindings = json.loads(checkpoint.execute("SELECT value FROM metadata WHERE key='bindings'").fetchone()[0])
        if hashlib.sha256(canonical(bindings)).hexdigest() != provenance["checkpoint_bindings_sha256"] or bindings["selection_sha256"] != selection_sha256:
            raise ValueError("checkpoint selection binding mismatch")
        for source_key, bound_key in (("source_manifest_sha256", "source_manifest_sha256"),
                                      ("summary_sha256", "extraction_summary_sha256"),
                                      ("state_db_sha256", "state_db_sha256"),
                                      ("auditor_sha256", "auditor_sha256")):
            if bindings[source_key] != provenance[bound_key]:
                raise ValueError(f"checkpoint {source_key} binding mismatch")
        count = 0
        for event_id, cell, ok, reason in checkpoint.execute("SELECT event_id,assigned_cell,ok,reason FROM events"):
            event = by_id.get(event_id.hex())
            if event is None or (event["assigned_cell"], event["recovered"], event["reason"]) != (cell, bool(ok), reason):
                raise ValueError("checkpoint event mismatch")
            count += 1
        if count != len(events):
            raise ValueError("checkpoint event count mismatch")
        for key, field in (("parent_object_index", "parent_objects_verified_total"),
                           ("parent_rows_verified_total", "parent_rows_verified_total")):
            if json.loads(checkpoint.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()[0]) != provenance[field]:
                raise ValueError(f"checkpoint {key} mismatch")
    result = {
        "schema_version": "aws-btc-s0-provenance-correction-v1",
        "scope": "assigned_cells_only",
        "provenance_sha256": ORIGINAL_SHA256,
        "checkpoint_sha256": sha256(checkpoint_path),
        "selection_sha256": selection_sha256,
        "corrected_assigned_cells": {cell: len(groups[cell]) for cell in CELLS},
        "sampled_unique_events": len(events),
        "fully_recovered": provenance["fully_recovered"],
        "checkpoint_events_match": True,
        "limitations": ["Corrects only the assigned_cells summary; it does not re-scan frozen transactions or decide S0."],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        with open(temporary, "xb") as handle:
            handle.write(canonical(result) + b"\n")
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = correct(args.provenance, args.checkpoint, args.output)
    print(json.dumps({"status": "corrected", "cells": result["corrected_assigned_cells"]}, sort_keys=True))


if __name__ == "__main__":
    main()
