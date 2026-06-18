"""Phase 10: Case study analysis for EGS predictions."""
import torch
import csv
import os
import sys

sys.path.insert(0, r"D:\Code\VSCode\Bitcoin_Transaction_Identification\scripts")
import _bootstrap  # noqa: F401

from btcaml.data.label_maps import LABEL_TO_ID_11, ID_TO_LABEL_11, RISK_GROUPS

RUN_DIR = "experiments/runs/20260618_060733_cbk_egs_seed3407"
DATA_PATH = "data/processed/protocols/class_balanced_khop.pt"
OUT_DIR = "experiments/case_studies"
os.makedirs(OUT_DIR, exist_ok=True)

data = torch.load(DATA_PATH, map_location="cpu", weights_only=False)
if isinstance(data, dict) and "data" in data:
    data = data["data"]

test_mask = data.test_mask.numpy().astype(bool)

pred_path = os.path.join(RUN_DIR, "edge_gated_sage", "evaluation", "test_predictions.csv")
preds = {}
for row in csv.DictReader(open(pred_path, encoding="utf-8")):
    nid = int(row["node_index"])
    preds[nid] = {
        "true": int(row["y_true"]),
        "pred": int(row["y_pred"]),
        "true_name": row["y_true_name"],
        "pred_name": row["y_pred_name"],
        "confidence": float(row["confidence"]),
    }

sensitive_ids = set()
for group in ["conservative_sensitive", "extended_sensitive"]:
    for cls in RISK_GROUPS.get(group, []):
        if cls in LABEL_TO_ID_11:
            sensitive_ids.add(LABEL_TO_ID_11[cls])

correct_sensitive = []
false_positive = []
false_negative = []
test_nodes = [i for i in range(len(test_mask)) if test_mask[i]]

for nid in test_nodes:
    if nid not in preds:
        continue
    p = preds[nid]
    t_s = p["true"] in sensitive_ids
    pr_s = p["pred"] in sensitive_ids
    case = {"node_id": nid, **p}
    if t_s and pr_s:
        correct_sensitive.append(case)
    elif not t_s and pr_s:
        false_positive.append(case)
    elif t_s and not pr_s:
        false_negative.append(case)

correct_sensitive.sort(key=lambda x: x["true_name"])
false_positive.sort(key=lambda x: x["pred_name"])
false_negative.sort(key=lambda x: x["true_name"])

with open(os.path.join(OUT_DIR, "case_study_report.md"), "w", encoding="utf-8") as f:
    f.write("# Case Study: EGS Prediction Analysis\n\n")
    f.write("## Model: EdgeGatedSAGE (seed=3407, class_balanced_khop)\n\n")
    f.write("- Test nodes: {}\n".format(len(test_nodes)))
    f.write("- Correctly identified sensitive: {}\n".format(len(correct_sensitive)))
    f.write("- False positives: {}\n".format(len(false_positive)))
    f.write("- False negatives (missed): {}\n\n".format(len(false_negative)))
    
    f.write("## Correctly Identified Sensitive Entities\n\n")
    by_cls = {}
    for c in correct_sensitive:
        by_cls.setdefault(c["true_name"], []).append(c)
    for cls in sorted(by_cls.keys()):
        items = by_cls[cls]
        f.write("### {} ({} correct)\n".format(cls, len(items)))
        for c in items[:5]:
            f.write("- Node {}: true={}, pred={}, conf={:.3f}\n".format(
                c["node_id"], c["true_name"], c["pred_name"], c["confidence"]))
        f.write("\n")
    
    f.write("## False Positives\n\n")
    by_cls = {}
    for c in false_positive:
        by_cls.setdefault(c["pred_name"], []).append(c)
    for cls in sorted(by_cls.keys()):
        items = by_cls[cls]
        f.write("### Predicted as {} ({} FP)\n".format(cls, len(items)))
        for c in items[:5]:
            f.write("- Node {}: true={}, pred={}, conf={:.3f}\n".format(
                c["node_id"], c["true_name"], c["pred_name"], c["confidence"]))
        f.write("\n")
    
    f.write("## False Negatives (Missed Sensitive)\n\n")
    by_cls = {}
    for c in false_negative:
        by_cls.setdefault(c["true_name"], []).append(c)
    for cls in sorted(by_cls.keys()):
        items = by_cls[cls]
        f.write("### {} ({} missed)\n".format(cls, len(items)))
        for c in items[:5]:
            f.write("- Node {}: true={}, pred={}, conf={:.3f}\n".format(
                c["node_id"], c["true_name"], c["pred_name"], c["confidence"]))
        f.write("\n")

print("Case study: correct_sens={} FP={} FN={}".format(
    len(correct_sensitive), len(false_positive), len(false_negative)))
print("Written to:", os.path.join(OUT_DIR, "case_study_report.md"))
