#!/usr/bin/env python3
"""Compare the two frozen S0 evaluation artifacts field by field.

Gate 3A v1.3 requires that two consecutive independent runs agree on file hash,
input bindings, every cell metric, the candidate decision and the boundary
fields. Any unexplained difference must stop the finalization instead of
selecting the better-looking run.
"""
import hashlib
import json
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cell_key(cell):
    return (cell["window_id"], cell["filter_profile"], cell["horizon_blocks"])


def flatten(cell):
    """Reduce a cell to the frozen comparable fields."""
    entry = {
        "support_sha256": cell["support_sha256"],
        "transaction_sha256": cell["transaction_sha256"],
        "partition_sha256": cell["partition_sha256"],
        "point": cell["point"],
        "secondary": cell["secondary"],
        "graphs": {name: value["sha256"] for name, value in cell["graphs"].items()},
        "graph_bytes": {name: value["bytes"] for name, value in cell["graphs"].items()},
        "graph_record_counts": {name: value["record_counts"] for name, value in cell["graphs"].items()},
    }
    for length, bootstrap in cell["bootstrap"].items():
        entry[f"bootstrap_{length}"] = {
            "cell_seed": bootstrap["cell_seed"],
            "replicates": bootstrap["replicates"],
            "resample_indices_sha256": bootstrap["resample_indices_sha256"],
            "p_merge_lower": bootstrap["p_merge"]["lower"],
            "p_merge_upper": bootstrap["p_merge"]["upper"],
            "p_rewrite_lower": bootstrap["p_rewrite"]["lower"],
            "p_rewrite_upper": bootstrap["p_rewrite"]["upper"],
        }
    return entry


def main():
    if len(sys.argv) != 3:
        print("usage: compare_s0_evaluations.py <evaluation_run01.json> <evaluation_run02.json>")
        return 2
    first, second = (Path(arg) for arg in sys.argv[1:3])
    hash_first, hash_second = sha256(first), sha256(second)
    report = {
        "run01": {"path": str(first), "sha256": hash_first},
        "run02": {"path": str(second), "sha256": hash_second},
        "byte_identical": hash_first == hash_second,
    }

    a = json.loads(first.read_text(encoding="utf-8"))
    b = json.loads(second.read_text(encoding="utf-8"))

    for field in ("protocol_version", "extractor_summary_sha256", "source_manifest_sha256",
                  "union_log_sha256", "seed", "runner_sha256", "environment", "inputs",
                  "effect_metrics_read", "labels_read", "models_authorized",
                  "integrity", "decision"):
        report[f"field::{field}"] = "identical" if a.get(field) == b.get(field) else "DIFFERENT"

    cells_a = {cell_key(c): c for c in a["cells"]}
    cells_b = {cell_key(c): c for c in b["cells"]}
    report["cell_count"] = {"run01": len(cells_a), "run02": len(cells_b),
                            "same_keys": set(cells_a) == set(cells_b)}
    differing = []
    for key in sorted(set(cells_a) & set(cells_b)):
        if flatten(cells_a[key]) != flatten(cells_b[key]):
            left, right = flatten(cells_a[key]), flatten(cells_b[key])
            fields = sorted({k for k in set(left) | set(right) if left.get(k) != right.get(k)})
            differing.append({"cell": list(key), "differing_fields": fields})
    report["cells_differing"] = differing
    report["all_cells_identical"] = not differing
    report["verdict"] = "AGREE" if (hash_first == hash_second and not differing
                                    and set(cells_a) == set(cells_b)) else "STOP_AND_AUDIT"

    out = Path(__file__).resolve().parent / "s0_evaluation_comparison.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "byte_identical": report["byte_identical"],
                      "cell_count": report["cell_count"], "cells_differing": len(differing),
                      "report": str(out)}, ensure_ascii=False))
    return 0 if report["verdict"] == "AGREE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
