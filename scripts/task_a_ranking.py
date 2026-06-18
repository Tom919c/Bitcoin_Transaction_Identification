"""Task A: Conservative Sensitive Ranking"""
import sys, os, gc
ROOT = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import torch
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score
from btcaml.data.label_maps import LABEL_TO_ID_11, RISK_GROUPS, RAW_LABELS_11
from btcaml.models.registry import build_model

print("=== Task A: Conservative Sensitive Ranking ===", flush=True)

payload = torch.load("data/processed/protocols/class_balanced_khop.pt", map_location="cpu", weights_only=False)
data = payload["data"] if isinstance(payload, dict) and "data" in payload else payload
y, test_mask, x, edge_index = data.y, data.test_mask, data.x, data.edge_index
edge_attr = data.edge_attr if hasattr(data, "edge_attr") else None

valid = test_mask & (y != -1)
test_idx = torch.where(valid)[0]
y_test = y[test_idx].numpy()
print(f"Test nodes: {len(y_test)}", flush=True)

cons_ids = [LABEL_TO_ID_11[c] for c in RISK_GROUPS["conservative_sensitive"]]
ext_ids = [LABEL_TO_ID_11[c] for c in RISK_GROUPS["extended_sensitive"]]
y_cons = np.isin(y_test, cons_ids).astype(int)
y_ext = np.isin(y_test, ext_ids).astype(int)
print(f"Conservative positives: {y_cons.sum()}, Extended positives: {y_ext.sum()}", flush=True)

runs = [
    ("seed42", "experiments/runs/20260618_050010_cbk_egs_seed42/edge_gated_sage/checkpoints/best.pt"),
    ("seed3407", "experiments/runs/20260618_060733_cbk_egs_seed3407/edge_gated_sage/checkpoints/best.pt"),
    ("seed1234", "experiments/runs/20260618_072448_cbk_egs_seed1234/edge_gated_sage/checkpoints/best.pt"),
]

params = {"hidden_channels": 128, "num_layers": 3, "dropout": 0.3, "edge_hidden": 64, "use_direction": True}
edge_dim = int(edge_attr.shape[1]) if edge_attr is not None else None

all_rows = []

for sname, ckpt_path in runs:
    print(f"\n--- {sname} ---", flush=True)
    model = build_model("edge_gated_sage", int(x.shape[1]), 11, edge_dim=edge_dim, params=params)
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    with torch.no_grad():
        logits = model(x, edge_index, edge_attr)
    probs = torch.softmax(logits[test_idx], dim=1).numpy()

    for group_name, y_bin, g_ids in [("conservative", y_cons, cons_ids), ("extended", y_ext, ext_ids)]:
        score = probs[:, g_ids].sum(axis=1)
        auprc = average_precision_score(y_bin, score)
        auroc = roc_auc_score(y_bin, score)
        for k_pct in [1, 5, 10]:
            k = max(1, int(len(score) * k_pct / 100))
            top_idx = np.argsort(score)[-k:]
            recall = y_bin[top_idx].sum() / max(y_bin.sum(), 1)
            precision = y_bin[top_idx].mean()
            yld = y_bin[top_idx].sum() / k
            all_rows.append({"group": group_name, "seed": sname, "k_pct": k_pct, "auprc": auprc, "auroc": auroc,
                             "recall": recall, "precision": precision, "yield": yld})
            print(f"  {group_name} k={k_pct}% auprc={auprc:.4f} auroc={auroc:.4f} recall={recall:.4f} prec={precision:.4f}", flush=True)
    del model, logits, probs; gc.collect()

out = Path("experiments/ranking"); out.mkdir(parents=True, exist_ok=True)
df = pd.DataFrame(all_rows)
df[df["group"]=="conservative"].to_csv(out/"conservative_sensitive_ranking.csv", index=False)
df[df["group"]=="extended"].to_csv(out/"extended_sensitive_ranking.csv", index=False)

# Summary
lines = ["# Sensitive Ranking Summary", ""]
for g in ["conservative", "extended"]:
    sub = df[df["group"]==g]
    lines.append(f"## {g.capitalize()} Sensitive")
    lines.append("")
    lines.append("| Seed | k% | AUPRC | AUROC | Recall | Precision | Yield |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, r in sub.iterrows():
        lines.append(f"| {r.seed} | {r.k_pct}% | {r.auprc:.4f} | {r.auroc:.4f} | {r.recall:.4f} | {r.precision:.4f} | {r['yield']:.4f} |")
    lines.append(f"\n**Mean AUPRC**: {sub['auprc'].mean():.4f} +/- {sub['auprc'].std():.4f}")
    lines.append(f"**Mean AUROC**: {sub['auroc'].mean():.4f} +/- {sub['auroc'].std():.4f}")
    lines.append("")

mc = df[df["group"]=="conservative"]["auprc"].mean()
me = df[df["group"]=="extended"]["auprc"].mean()
lines.append("## Analysis")
lines.append("")
lines.append(f"Conservative mean AUPRC: {mc:.4f}")
lines.append(f"Extended mean AUPRC: {me:.4f}")
lines.append(f"Difference: {me-mc:.4f}")
lines.append("")
if me - mc > 0.1:
    lines.append("Extended ranking significantly outperforms conservative, indicating BET/GAMBLING dominate ranking signal.")
else:
    lines.append("Conservative and extended rankings are close; model ranking is not solely driven by easy classes.")
lines.append("")
if mc > 0.5:
    lines.append("Conservative AUPRC > 0.5: meaningful risk ranking for high-sensitivity AML classes.")
    lines.append("Risk ranking can serve as application contribution (validate with case studies).")
elif mc > 0.3:
    lines.append("Conservative AUPRC 0.3-0.5: moderate ranking ability, should not overstate application value.")
else:
    lines.append("Conservative AUPRC < 0.3: limited ranking capability for high-sensitivity AML classes.")
    lines.append("Current model should not overstate application value for conservative AML risk detection.")
(out/"sensitive_ranking_summary.md").write_text("\n".join(lines), encoding="utf-8")
print(f"\nSaved to {out}", flush=True)
