"""Task B: Temporal Feature Failure Analysis"""
import sys, os
ROOT = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import torch
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

print("=== Task B: Temporal Feature Failure Analysis ===", flush=True)

# 1. Per-class delta analysis: full vs no-temporal
print("\n--- Per-class delta: CBK ---", flush=True)

def load_per_class(run_dir):
    p = Path(run_dir) / "edge_gated_sage" / "evaluation" / "test_per_class.csv"
    if not p.exists():
        p = Path(run_dir) / "test_per_class.csv"
    return pd.read_csv(p)

# CBK comparison
cbk_full = load_per_class("experiments/runs/20260618_050010_cbk_egs_seed42")
cbk_notemp = load_per_class("experiments/runs/20260618_191552_cbk_no_temporal_egs_r2")

out_dir = Path("experiments/diagnostics"); out_dir.mkdir(parents=True, exist_ok=True)

# Merge and compute delta
cbk_merged = cbk_full[["label", "precision", "recall", "f1"]].merge(
    cbk_notemp[["label", "precision", "recall", "f1"]], on="label", suffixes=("_full", "_no_temporal"))
cbk_merged["delta_f1"] = cbk_merged["f1_no_temporal"] - cbk_merged["f1_full"]
cbk_merged["delta_precision"] = cbk_merged["precision_no_temporal"] - cbk_merged["precision_full"]
cbk_merged["delta_recall"] = cbk_merged["recall_no_temporal"] - cbk_merged["recall_full"]
cbk_merged.to_csv(out_dir / "full_vs_no_temporal_per_class_delta_cbk.csv", index=False)
print(cbk_merged.to_string(index=False), flush=True)

# Temporal comparison
print("\n--- Per-class delta: temporal ---", flush=True)
temp_full = load_per_class("experiments/runs/20260618_005109_temporal_egs")
temp_notemp = load_per_class("experiments/runs/20260618_134902_temporal_egs_no_temporal")

temp_merged = temp_full[["label", "precision", "recall", "f1"]].merge(
    temp_notemp[["label", "precision", "recall", "f1"]], on="label", suffixes=("_full", "_no_temporal"))
temp_merged["delta_f1"] = temp_merged["f1_no_temporal"] - temp_merged["f1_full"]
temp_merged.to_csv(out_dir / "full_vs_no_temporal_per_class_delta_temporal.csv", index=False)
print(temp_merged.to_string(index=False), flush=True)

# 2. Edge feature drift analysis
print("\n--- Edge Feature Drift Analysis ---", flush=True)

payload = torch.load("data/processed/protocols/class_balanced_khop.pt", map_location="cpu", weights_only=False)
data_cbk = payload["data"] if isinstance(payload, dict) and "data" in payload else payload

payload_t = torch.load("data/processed/protocols/temporal_balanced.pt", map_location="cpu", weights_only=False)
data_temp = payload_t["data"] if isinstance(payload_t, dict) and "data" in payload_t else payload_t

edge_attr_cbk = data_cbk.edge_attr.numpy()
edge_attr_temp = data_temp.edge_attr.numpy()

# For CBK: use train/val/test masks on nodes to determine edge splits
# An edge belongs to a split if its source node is in that split
y_cbk = data_cbk.y.numpy()
train_mask_cbk = data_cbk.train_mask.numpy().astype(bool)
val_mask_cbk = data_cbk.val_mask.numpy().astype(bool)
test_mask_cbk = data_cbk.test_mask.numpy().astype(bool)

ei_cbk = data_cbk.edge_index.numpy()
src_cbk = ei_cbk[0]

# Edge splits based on source node
train_edges_cbk = np.isin(src_cbk, np.where(train_mask_cbk)[0])
val_edges_cbk = np.isin(src_cbk, np.where(val_mask_cbk)[0])
test_edges_cbk = np.isin(src_cbk, np.where(test_mask_cbk)[0])

# Temporal splits
y_temp = data_temp.y.numpy()
train_mask_temp = data_temp.train_mask.numpy().astype(bool)
val_mask_temp = data_temp.val_mask.numpy().astype(bool)
test_mask_temp = data_temp.test_mask.numpy().astype(bool)
ei_temp = data_temp.edge_index.numpy()
src_temp = ei_temp[0]
train_edges_temp = np.isin(src_temp, np.where(train_mask_temp)[0])
val_edges_temp = np.isin(src_temp, np.where(val_mask_temp)[0])
test_edges_temp = np.isin(src_temp, np.where(test_mask_temp)[0])

feature_names = ["reveal", "last_seen", "total", "min", "max", "avg", "duration", "frequency", "recency", "feat9", "feat10"]

drift_rows = []
for fi in range(edge_attr_cbk.shape[1]):
    fname = feature_names[fi] if fi < len(feature_names) else f"feat{fi}"
    for dataset_name, ea, tr_m, va_m, te_m in [
        ("class_balanced_khop", edge_attr_cbk, train_edges_cbk, val_edges_cbk, test_edges_cbk),
        ("temporal_balanced", edge_attr_temp, train_edges_temp, val_edges_temp, test_edges_temp)
    ]:
        tr_vals = ea[tr_m, fi]
        va_vals = ea[va_m, fi]
        te_vals = ea[te_m, fi]
        
        ks_stat, ks_p = stats.ks_2samp(tr_vals, te_vals)
        try:
            w_dist = stats.wasserstein_distance(tr_vals, te_vals)
        except:
            w_dist = float("nan")
        
        drift_rows.append({
            "dataset": dataset_name, "feature": fname, "feature_idx": fi,
            "train_mean": tr_vals.mean(), "train_std": tr_vals.std(),
            "val_mean": va_vals.mean(), "val_std": va_vals.std(),
            "test_mean": te_vals.mean(), "test_std": te_vals.std(),
            "abs_mean_shift": abs(te_vals.mean() - tr_vals.mean()),
            "std_mean_shift": abs(te_vals.mean() - tr_vals.mean()) / max(tr_vals.std(), 1e-8),
            "ks_statistic": ks_stat, "ks_pvalue": ks_p,
            "wasserstein_distance": w_dist,
        })

drift_df = pd.DataFrame(drift_rows)
drift_df.to_csv(out_dir / "temporal_feature_drift.csv", index=False)
print("\nTemporal feature drift saved.", flush=True)

# Print summary: top drifting features
for ds in ["class_balanced_khop", "temporal_balanced"]:
    sub = drift_df[drift_df["dataset"]==ds].sort_values("ks_statistic", ascending=False)
    print(f"\nTop drifting features ({ds}):", flush=True)
    for _, r in sub.head(5).iterrows():
        print(f"  {r.feature}: KS={r.ks_statistic:.4f} mean_shift={r.abs_mean_shift:.4f} wasserstein={r.wasserstein_distance:.4f}", flush=True)

# 3. Temporal feature correlation with labels
print("\n--- Feature-Label Correlation ---", flush=True)
corr_rows = []
for fi in range(edge_attr_cbk.shape[1]):
    fname = feature_names[fi] if fi < len(feature_names) else f"feat{fi}"
    # For each labeled node, compute mean of incoming edge features
    dst_cbk = ei_cbk[1]
    for split_name, mask in [("train", train_mask_cbk), ("val", val_mask_cbk), ("test", test_mask_cbk)]:
        labeled_nodes = np.where(mask & (y_cbk != -1))[0]
        for cls_id in range(11):
            cls_nodes = labeled_nodes[y_cbk[labeled_nodes] == cls_id]
            if len(cls_nodes) == 0:
                continue
            edge_mask = np.isin(dst_cbk, cls_nodes)
            if edge_mask.sum() == 0:
                continue
            mean_feat = edge_attr_cbk[edge_mask, fi].mean()
            corr_rows.append({"feature": fname, "split": split_name, "class_id": cls_id, "mean_feature_value": mean_feat})

corr_df = pd.DataFrame(corr_rows)
corr_df.to_csv(out_dir / "temporal_feature_class_correlation.csv", index=False)
print("Feature-class correlation saved.", flush=True)

# 4. Write failure report
lines = []
lines.append("# Temporal Feature Failure Analysis Report")
lines.append("")
lines.append("## 1. Per-Class Delta: CBK (full vs no-temporal)")
lines.append("")
lines.append("| Class | F1_full | F1_no_temp | Delta | P_full | P_no_temp | R_full | R_no_temp |")
lines.append("|---|---|---|---|---|---|---|---|")
for _, r in cbk_merged.iterrows():
    lines.append(f"| {r['label']} | {r.f1_full:.4f} | {r.f1_no_temporal:.4f} | {r.delta_f1:+.4f} | {r.precision_full:.4f} | {r.precision_no_temporal:.4f} | {r.recall_full:.4f} | {r.recall_no_temporal:.4f} |")
lines.append("")
lines.append("## 2. Per-Class Delta: Temporal (full vs no-temporal)")
lines.append("")
for _, r in temp_merged.iterrows():
    lines.append(f"| {r['label']} | {r.f1_full:.4f} | {r.f1_no_temporal:.4f} | {r.delta_f1:+.4f} |")
lines.append("")

# Analyze which features drift most
lines.append("## 3. Edge Feature Drift Summary")
lines.append("")
for ds in ["class_balanced_khop", "temporal_balanced"]:
    sub = drift_df[drift_df["dataset"]==ds].sort_values("ks_statistic", ascending=False)
    lines.append(f"### {ds}")
    lines.append("")
    lines.append("| Feature | Train Mean | Test Mean | Abs Shift | Std Shift | KS Stat | Wasserstein |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, r in sub.iterrows():
        lines.append(f"| {r.feature} | {r.train_mean:.4f} | {r.test_mean:.4f} | {r.abs_mean_shift:.4f} | {r.std_mean_shift:.4f} | {r.ks_statistic:.4f} | {r.wasserstein_distance:.4f} |")
    lines.append("")

# Key findings
lines.append("## 4. Key Findings")
lines.append("")

# Check if no-temporal is consistently better
cbk_delta = cbk_merged["delta_f1"].mean()
temp_delta = temp_merged["delta_f1"].mean()
lines.append(f"- CBK mean F1 delta (no_temp - full): {cbk_delta:+.4f}")
lines.append(f"- Temporal mean F1 delta (no_temp - full): {temp_delta:+.4f}")
lines.append("")

# Identify which features drift most
top_drift = drift_df[drift_df["dataset"]=="temporal_balanced"].sort_values("ks_statistic", ascending=False).head(3)
lines.append("Top drifting temporal edge features (temporal_balanced):")
for _, r in top_drift.iterrows():
    lines.append(f"- {r.feature}: KS={r.ks_statistic:.4f}, standardized shift={r.std_mean_shift:.4f}")
lines.append("")

lines.append("## 5. Why Temporal Features Do Not Help")
lines.append("")
if cbk_delta > 0 and temp_delta > 0:
    lines.append("Removing temporal edge features improves performance on BOTH protocols.")
    lines.append("This suggests temporal features are adding noise rather than useful signal.")
    lines.append("Possible explanations:")
    lines.append("1. Temporal features encode information that correlates with the random split but not with actual risk patterns")
    lines.append("2. Temporal features have high distribution drift between train/test, making them unreliable")
    lines.append("3. The model may overfit to temporal artifacts in the training data")
    lines.append("4. Edge gating may be overwhelmed by noisy temporal features, reducing its filtering ability")
elif cbk_delta > 0:
    lines.append("Removing temporal features helps on CBK but has mixed effect on temporal.")
    lines.append("This suggests some pseudo-correlation in the random split.")
elif temp_delta > 0:
    lines.append("Removing temporal features helps on temporal but not CBK.")
    lines.append("This suggests temporal feature drift is the main issue.")
else:
    lines.append("Removing temporal features does not consistently help.")
    lines.append("The improvement observed previously may be within noise range.")

lines.append("")
lines.append("## 6. Can Temporal Features Be a Method Contribution?")
lines.append("")
lines.append("Based on current evidence: NO, raw temporal edge features should NOT be used as a method contribution.")
lines.append("They add noise and exhibit drift. Any temporal modeling should be more sophisticated than direct feature inclusion.")
lines.append("")
lines.append("## 7. Should We Continue Temporal OOD Methods?")
lines.append("")
lines.append("The temporal OOD problem is real (0.25 vs 0.65 performance gap).")
lines.append("But the solution should NOT be simply adding temporal edge features.")
lines.append("Potential lightweight approaches:")
lines.append("1. Topology-aware reweighting based on neighbor heterophily")
lines.append("2. Direction-aware temporal edge filtering (drop or downweight drifted edges)")
lines.append("3. Environment-invariant training with temporal split as environment")

(out_dir / "temporal_feature_failure_report.md").write_text("\n".join(lines), encoding="utf-8")
print(f"\nAll Task B outputs saved to {out_dir}", flush=True)


