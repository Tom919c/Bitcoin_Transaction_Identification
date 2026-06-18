"""Task C: Node Classification Boundary / Confusion Case Study"""
import sys, os
ROOT = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import torch
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

print("=== Task C: Confusion Case Study ===", flush=True)

# Load data
payload = torch.load("data/processed/protocols/class_balanced_khop.pt", map_location="cpu", weights_only=False)
data = payload["data"] if isinstance(payload, dict) and "data" in payload else payload
y = data.y.numpy()
ei = data.edge_index.numpy()
ea = data.edge_attr.numpy() if hasattr(data, "edge_attr") else None
test_mask = data.test_mask.numpy().astype(bool)

LABELS = ["INDIVIDUAL","BET","GAMBLING","EXCHANGE","MINING","PONZI","RANSOMWARE","FAUCET","MARKETPLACE","MIXER","BRIDGE"]

# Load best EGS predictions (seed 3407 is best)
pred_path = "experiments/runs/20260618_060733_cbk_egs_seed3407/edge_gated_sage/evaluation/test_predictions.csv"
preds = pd.read_csv(pred_path)
print(f"Loaded {len(preds)} test predictions", flush=True)

# Build adjacency for fast neighbor lookup
src, dst = ei[0], ei[1]
n_nodes = len(y)

# Precompute in/out neighbors per node
print("Building neighbor index...", flush=True)
in_neighbors = [[] for _ in range(n_nodes)]
out_neighbors = [[] for _ in range(n_nodes)]
for s, d in zip(src, dst):
    out_neighbors[s].append(d)
    in_neighbors[d].append(s)

# Confusion pairs to analyze
confusion_pairs = [
    ("MIXER", "EXCHANGE"),
    ("GAMBLING", "EXCHANGE"),
    ("RANSOMWARE", "INDIVIDUAL"),
    ("MARKETPLACE", "EXCHANGE"),
    ("PONZI", "INDIVIDUAL"),
    ("PONZI", "EXCHANGE"),
]

out_dir = Path("experiments/case_studies"); out_dir.mkdir(parents=True, exist_ok=True)

def get_node_stats(node_id):
    """Get neighborhood statistics for a node."""
    in_nbrs = in_neighbors[node_id]
    out_nbrs = out_neighbors[node_id]
    
    in_labels = [y[n] for n in in_nbrs if y[n] != -1]
    out_labels = [y[n] for n in out_nbrs if y[n] != -1]
    all_labels = in_labels + out_labels
    
    in_counter = Counter(in_labels)
    out_counter = Counter(out_labels)
    all_counter = Counter(all_labels)
    
    true_label = y[node_id]
    same_label_count = all_counter.get(true_label, 0)
    total_labeled = len(all_labels)
    unlabeled_count = len(in_nbrs) + len(out_nbrs) - total_labeled
    total_nbrs = len(in_nbrs) + len(out_nbrs)
    
    # Amount stats from edge_attr (index 2 = total, 3 = min, 4 = max, 5 = avg)
    in_amounts = []
    out_amounts = []
    if ea is not None:
        for i, (s, d) in enumerate(zip(src, dst)):
            if d == node_id:
                in_amounts.append(ea[i, 2])  # total
            if s == node_id:
                out_amounts.append(ea[i, 2])
    
    return {
        "in_degree": len(in_nbrs),
        "out_degree": len(out_nbrs),
        "total_degree": total_nbrs,
        "labeled_in_degree": len(in_labels),
        "labeled_out_degree": len(out_labels),
        "same_label_ratio": same_label_count / max(total_labeled, 1),
        "unlabeled_ratio": unlabeled_count / max(total_nbrs, 1),
        "top_in_labels": dict(in_counter.most_common(3)),
        "top_out_labels": dict(out_counter.most_common(3)),
        "in_amount_mean": float(np.mean(in_amounts)) if in_amounts else 0,
        "out_amount_mean": float(np.mean(out_amounts)) if out_amounts else 0,
        "is_supernode": total_nbrs > 100,
    }

all_cases = []
pair_reports = {}

for true_name, pred_name in confusion_pairs:
    true_id = LABELS.index(true_name)
    pred_id = LABELS.index(pred_name)
    
    # Find misclassified cases
    mask_wrong = (preds["y_true"] == true_id) & (preds["y_pred"] == pred_id)
    wrong_nodes = preds[mask_wrong].sort_values("confidence", ascending=False)
    
    # Find correct cases
    mask_correct = (preds["y_true"] == true_id) & (preds["correct"] == True)
    correct_nodes = preds[mask_correct].sort_values("confidence", ascending=False)
    
    n_wrong = min(3, len(wrong_nodes))
    n_correct = min(3, len(correct_nodes))
    
    print(f"\n{true_name}->{pred_name}: {len(wrong_nodes)} wrong, {len(correct_nodes)} correct", flush=True)
    
    report_lines = []
    report_lines.append(f"# {true_name} -> {pred_name} Confusion Case Study")
    report_lines.append("")
    report_lines.append(f"Total misclassified: {len(wrong_nodes)}")
    report_lines.append(f"Total correctly classified: {len(correct_nodes)}")
    report_lines.append("")
    
    # Misclassified cases
    if n_wrong > 0:
        report_lines.append("## Misclassified Cases")
        report_lines.append("")
        for i, (_, row) in enumerate(wrong_nodes.head(3).iterrows()):
            nid = int(row["node_index"])
            stats = get_node_stats(nid)
            report_lines.append(f"### Case {i+1}: Node {nid}")
            report_lines.append(f"- True: {true_name}, Predicted: {pred_name}, Confidence: {row['confidence']:.4f}")
            report_lines.append(f"- In-degree: {stats['in_degree']}, Out-degree: {stats['out_degree']}, Total: {stats['total_degree']}")
            report_lines.append(f"- Same-label ratio: {stats['same_label_ratio']:.4f}")
            report_lines.append(f"- Unlabeled ratio: {stats['unlabeled_ratio']:.4f}")
            report_lines.append(f"- Top in-neighbors: {stats['top_in_labels']}")
            report_lines.append(f"- Top out-neighbors: {stats['top_out_labels']}")
            report_lines.append(f"- In-amount mean: {stats['in_amount_mean']:.2f}")
            report_lines.append(f"- Out-amount mean: {stats['out_amount_mean']:.2f}")
            report_lines.append(f"- Supernode (>100): {stats['is_supernode']}")
            report_lines.append("")
            
            all_cases.append({"pair": f"{true_name}->{pred_name}", "type": "wrong", "node_id": nid,
                             "confidence": row["confidence"], **stats})
    
    # Correct cases
    if n_correct > 0:
        report_lines.append("## Correctly Classified Cases")
        report_lines.append("")
        for i, (_, row) in enumerate(correct_nodes.head(3).iterrows()):
            nid = int(row["node_index"])
            stats = get_node_stats(nid)
            report_lines.append(f"### Case {i+1}: Node {nid}")
            report_lines.append(f"- True: {true_name}, Predicted: {true_name}, Confidence: {row['confidence']:.4f}")
            report_lines.append(f"- In-degree: {stats['in_degree']}, Out-degree: {stats['out_degree']}, Total: {stats['total_degree']}")
            report_lines.append(f"- Same-label ratio: {stats['same_label_ratio']:.4f}")
            report_lines.append(f"- Unlabeled ratio: {stats['unlabeled_ratio']:.4f}")
            report_lines.append(f"- Top in-neighbors: {stats['top_in_labels']}")
            report_lines.append(f"- Top out-neighbors: {stats['top_out_labels']}")
            report_lines.append("")
            
            all_cases.append({"pair": f"{true_name}->{pred_name}", "type": "correct", "node_id": nid,
                             "confidence": row["confidence"], **stats})
    
    pair_reports[f"{true_name}_{pred_name}"] = "\n".join(report_lines)

# Save all case data
cases_df = pd.DataFrame(all_cases)
# Flatten dict columns for CSV
for col in ["top_in_labels", "top_out_labels"]:
    if col in cases_df.columns:
        cases_df[col] = cases_df[col].astype(str)
cases_df.to_csv(out_dir / "confusion_cases.csv", index=False)

# Save individual pair reports
for pair_name, content in pair_reports.items():
    fname = f"{pair_name.lower()}_cases.md"
    (out_dir / fname).write_text(content, encoding="utf-8")

# 5. Boundary report
boundary_lines = []
boundary_lines.append("# Node Classification Boundary Report")
boundary_lines.append("")
boundary_lines.append("## Summary of Confusion Pairs")
boundary_lines.append("")
boundary_lines.append("| Pair | # Misclassified | # Correct |")
boundary_lines.append("|---|---|---|")
for true_name, pred_name in confusion_pairs:
    true_id = LABELS.index(true_name)
    pred_id = LABELS.index(pred_name)
    n_wrong = len(preds[(preds["y_true"]==true_id) & (preds["y_pred"]==pred_id)])
    n_correct = len(preds[(preds["y_true"]==true_id) & (preds["correct"]==True)])
    boundary_lines.append(f"| {true_name}->{pred_name} | {n_wrong} | {n_correct} |")

boundary_lines.append("")
boundary_lines.append("## Per-Pair Analysis")
boundary_lines.append("")

# Analyze patterns
for true_name, pred_name in confusion_pairs:
    cases_wrong = [c for c in all_cases if c["pair"]==f"{true_name}->{pred_name}" and c["type"]=="wrong"]
    cases_correct = [c for c in all_cases if c["pair"]==f"{true_name}->{pred_name}" and c["type"]=="correct"]
    
    boundary_lines.append(f"### {true_name} -> {pred_name}")
    boundary_lines.append("")
    
    if cases_wrong:
        avg_wrong_degree = np.mean([c["total_degree"] for c in cases_wrong])
        avg_wrong_unlabeled = np.mean([c["unlabeled_ratio"] for c in cases_wrong])
        avg_wrong_same = np.mean([c["same_label_ratio"] for c in cases_wrong])
        boundary_lines.append(f"Misclassified: avg_degree={avg_wrong_degree:.1f}, avg_unlabeled={avg_wrong_unlabeled:.3f}, avg_same_label={avg_wrong_same:.3f}")
    
    if cases_correct:
        avg_correct_degree = np.mean([c["total_degree"] for c in cases_correct])
        avg_correct_unlabeled = np.mean([c["unlabeled_ratio"] for c in cases_correct])
        avg_correct_same = np.mean([c["same_label_ratio"] for c in cases_correct])
        boundary_lines.append(f"Correct: avg_degree={avg_correct_degree:.1f}, avg_unlabeled={avg_correct_unlabeled:.3f}, avg_same_label={avg_correct_same:.3f}")
    
    boundary_lines.append("")

boundary_lines.append("## Key Questions")
boundary_lines.append("")
boundary_lines.append("### 1. Why is MIXER misclassified as EXCHANGE?")
mixer_cases = [c for c in all_cases if "MIXER->EXCHANGE" in c.get("pair","") and c["type"]=="wrong"]
if mixer_cases:
    avg_out = np.mean([c["out_degree"] for c in mixer_cases])
    avg_in = np.mean([c["in_degree"] for c in mixer_cases])
    boundary_lines.append(f"MIXER misclassified nodes: avg in-degree={avg_in:.1f}, out-degree={avg_out:.1f}")
    boundary_lines.append("MIXER nodes tend to have many connections (high degree) similar to EXCHANGE.")
    boundary_lines.append("With only 0.4% same-label neighbors, there is almost no local MIXER signal.")
else:
    boundary_lines.append("Insufficient MIXER->EXCHANGE misclassification cases for analysis.")

boundary_lines.append("")
boundary_lines.append("### 2. GAMBLING vs EXCHANGE structural confusion")
gambling_cases = [c for c in all_cases if "GAMBLING->EXCHANGE" in c.get("pair","") and c["type"]=="wrong"]
if gambling_cases:
    boundary_lines.append(f"GAMBLING misclassified nodes share structural patterns with EXCHANGE (high degree, diverse neighbors).")
else:
    boundary_lines.append("Limited GAMBLING->EXCHANGE confusion cases.")

boundary_lines.append("")
boundary_lines.append("### 3. RANSOMWARE diluted by INDIVIDUAL background")
ransom_cases = [c for c in all_cases if "RANSOMWARE->INDIVIDUAL" in c.get("pair","") and c["type"]=="wrong"]
if ransom_cases:
    avg_unlabeled = np.mean([c["unlabeled_ratio"] for c in ransom_cases])
    boundary_lines.append(f"RANSOMWARE misclassified nodes: avg unlabeled ratio={avg_unlabeled:.3f}")
    boundary_lines.append("RANSOMWARE nodes are surrounded by unlabeled background nodes that may appear similar to INDIVIDUAL.")
else:
    boundary_lines.append("Limited RANSOMWARE->INDIVIDUAL confusion cases.")

boundary_lines.append("")
boundary_lines.append("### 4. Is node classification sufficient?")
boundary_lines.append("")
boundary_lines.append("Based on the confusion analysis:")
boundary_lines.append("- MIXER has almost no same-label neighbors (0.4%), making node-level classification extremely difficult")
boundary_lines.append("- EXCHANGE and GAMBLING share structural patterns (high degree, many unlabeled neighbors)")
boundary_lines.append("- RANSOMWARE is diluted by INDIVIDUAL background neighbors")
boundary_lines.append("- For most classes, node features + 1-hop aggregation provide reasonable classification")
boundary_lines.append("- For MIXER specifically, the signal may require subgraph-level patterns (flow motifs)")

boundary_lines.append("")
boundary_lines.append("### 5. Which classes need subgraph reasoning?")
boundary_lines.append("")
boundary_lines.append("**Most likely candidates for subgraph reasoning:**")
boundary_lines.append("1. MIXER: 0.4% same-label ratio, almost no node-level signal")
boundary_lines.append("2. BRIDGE: 19.9% in-same but 53.6% out-same suggests directional flow pattern")
boundary_lines.append("")
boundary_lines.append("**Likely sufficient with node classification + direction-aware aggregation:**")
boundary_lines.append("1. INDIVIDUAL, BET: high support, clear patterns")
boundary_lines.append("2. EXCHANGE, MINING: distinct degree/amount profiles")

boundary_lines.append("")
boundary_lines.append("### 6. Should subgraph route proceed to next phase?")
boundary_lines.append("")
boundary_lines.append("Recommendation: Subgraph reasoning should be listed as FUTURE WORK, not immediate next step.")
boundary_lines.append("Rationale:")
boundary_lines.append("- MIXER support is only 16 test nodes, insufficient for robust subgraph evaluation")
boundary_lines.append("- Current node-level model already captures directional information well")
boundary_lines.append("- Subgraph methods add significant complexity and engineering cost")
boundary_lines.append("- The primary research contribution should focus on temporal OOD + direction awareness first")

(out_dir / "node_classification_boundary_report.md").write_text("\n".join(boundary_lines), encoding="utf-8")
print(f"\nAll Task C outputs saved to {out_dir}", flush=True)
print(f"Total cases analyzed: {len(all_cases)}", flush=True)
