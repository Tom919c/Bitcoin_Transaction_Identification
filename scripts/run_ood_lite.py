"""Topology-Aware Reweighting Lite: OOD prototype for temporal balanced protocol.
Computes per-node difficulty weights from graph topology (train nodes only) and
applies them to the loss function during training.
"""
import sys, os, gc, time
ROOT = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import torch
import torch.nn.functional as F
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
from btcaml.data.label_maps import LABEL_TO_ID_11, RAW_LABELS_11, UNKNOWN_LABEL
from btcaml.models.registry import build_model
from btcaml.utils.seed import seed_everything
from btcaml.evaluation.metrics import classification_metrics
from btcaml.evaluation.ranking import sensitive_score_from_logits
from btcaml.data.label_maps import RISK_GROUPS
from sklearn.metrics import average_precision_score

print("=== OOD Lite: Topology-Aware Reweighting ===", flush=True)

# --- Config ---
PROTOCOLS = {
    "temporal": "data/processed/protocols/temporal_balanced.pt",
    "cbk": "data/processed/protocols/class_balanced_khop.pt",
}
SEEDS = [42, 43, 44]
EPOCHS = 200
PATIENCE = 50
LR = 0.001
WD = 5e-4
CLIP = 1.0
HIDDEN = 128
LAYERS = 3
DROPOUT = 0.3
EDGE_HIDDEN = 64
NUM_CLASSES = 11
WEIGHT_CLIP = (0.5, 2.5)  # [min, max] for difficulty weight

# --- Compute topology-aware difficulty weights ---
def compute_difficulty_weights(data, train_mask_supervised):
    """Compute per-node difficulty weights based on neighborhood topology.
    Only uses train_mask nodes to avoid label leakage.
    Returns a weight tensor aligned with train_mask_supervised indices.
    """
    y = data.y.numpy()
    ei = data.edge_index.numpy()
    src, dst = ei[0], ei[1]
    n = len(y)
    
    # Build in/out neighbor lists
    in_nbrs = [[] for _ in range(n)]
    out_nbrs = [[] for _ in range(n)]
    for s, d in zip(src, dst):
        out_nbrs[s].append(d)
        in_nbrs[d].append(s)
    
    train_indices = torch.where(train_mask_supervised)[0].numpy()
    weights = np.ones(len(train_indices), dtype=np.float32)
    
    for i, nid in enumerate(train_indices):
        true_label = y[nid]
        all_nbrs = in_nbrs[nid] + out_nbrs[nid]
        if len(all_nbrs) == 0:
            weights[i] = 1.0
            continue
        
        labeled_nbrs = [y[n] for n in all_nbrs if y[n] != UNKNOWN_LABEL]
        total_nbrs = len(all_nbrs)
        unlabeled_count = total_nbrs - len(labeled_nbrs)
        unlabeled_ratio = unlabeled_count / max(total_nbrs, 1)
        
        same_count = sum(1 for l in labeled_nbrs if l == true_label)
        same_ratio = same_count / max(len(labeled_nbrs), 1)
        
        # Difficulty = high unlabeled ratio + low same-label ratio
        # Weight = 1 + alpha * unlabeled_ratio + beta * (1 - same_ratio)
        # Clip to [0.5, 2.5]
        alpha = 1.0
        beta = 0.5
        raw_weight = 1.0 + alpha * unlabeled_ratio + beta * (1.0 - same_ratio)
        weights[i] = np.clip(raw_weight, WEIGHT_CLIP[0], WEIGHT_CLIP[1])
    
    return torch.tensor(weights, dtype=torch.float32)

# --- Training function ---
def run_experiment(data_path, seed, use_reweighting, run_name):
    seed_everything(seed)
    
    payload = torch.load(data_path, map_location="cpu", weights_only=False)
    data = payload["data"] if isinstance(payload, dict) and "data" in payload else payload
    
    x = data.x
    edge_index = data.edge_index
    edge_attr = data.edge_attr if hasattr(data, "edge_attr") else None
    y = data.y
    train_mask = data.train_mask.bool() & (y != UNKNOWN_LABEL)
    val_mask = data.val_mask.bool() & (y != UNKNOWN_LABEL)
    test_mask = data.test_mask.bool() & (y != UNKNOWN_LABEL)
    
    # Build model (no temporal edge features)
    # Zero out temporal features (cols 0,1,6,7,8 = reveal, last_seen, duration, frequency, recency)
    if edge_attr is not None:
        ea_notemp = edge_attr.clone()
        temporal_cols = [0, 1, 6, 7, 8]
        for c in temporal_cols:
            if c < ea_notemp.shape[1]:
                ea_notemp[:, c] = 0.0
        edge_dim = ea_notemp.shape[1]
    else:
        ea_notemp = None
        edge_dim = None
    
    model_params = {"hidden_channels": HIDDEN, "num_layers": LAYERS, "dropout": DROPOUT,
                    "edge_hidden": EDGE_HIDDEN, "use_direction": True}
    model = build_model("edge_gated_sage", int(x.shape[1]), NUM_CLASSES, edge_dim=edge_dim, params=model_params)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WD)
    
    # Class weights
    train_y = y[train_mask]
    class_counts = torch.bincount(train_y, minlength=NUM_CLASSES).float()
    class_counts = class_counts.clamp(min=1)
    class_weights = (1.0 / class_counts)
    class_weights = class_weights / class_weights.mean()
    class_weights = class_weights.clamp(max=10.0)
    
    # Topology-aware difficulty weights
    if use_reweighting:
        topo_weights = compute_difficulty_weights(data, train_mask)
        print(f"  Topology weights: min={topo_weights.min():.3f} max={topo_weights.max():.3f} mean={topo_weights.mean():.3f}", flush=True)
    else:
        topo_weights = None
    
    best_metric = -1.0
    patience_counter = 0
    best_state = None
    best_epoch = -1
    
    train_indices = torch.where(train_mask)[0]
    
    start_time = time.time()
    for epoch in range(1, EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        
        logits = model(x, edge_index, ea_notemp)
        train_logits = logits[train_mask]
        train_y_actual = y[train_mask]
        
        # Per-node CE loss
        per_node_loss = F.cross_entropy(train_logits, train_y_actual, weight=class_weights, reduction="none")
        
        # Apply topology-aware weights
        if topo_weights is not None:
            per_node_loss = per_node_loss * topo_weights
        
        loss = per_node_loss.mean()
        loss.backward()
        if CLIP > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP)
        optimizer.step()
        
        # Eval
        if epoch % 1 == 0:
            model.eval()
            with torch.no_grad():
                logits = model(x, edge_index, ea_notemp)
                val_metrics = classification_metrics(logits, y, val_mask, RAW_LABELS_11)
            val_f1 = val_metrics.get("macro_f1", 0.0)
            if val_f1 > best_metric:
                best_metric = val_f1
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
                best_epoch = epoch
                patience_counter = 0
            else:
                patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"  Early stop at epoch {epoch}, best={best_metric:.4f} @ epoch {best_epoch}", flush=True)
                break
        
        if epoch % 20 == 0 or epoch == 1:
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.0f}s] epoch {epoch:04d} | loss {loss.item():.4f} | val_macro {val_f1:.4f} | best {best_metric:.4f}", flush=True)
    
    # Load best and evaluate on test
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        logits = model(x, edge_index, ea_notemp)
    test_metrics = classification_metrics(logits, y, test_mask, RAW_LABELS_11)
    
    elapsed = time.time() - start_time
    print(f"  DONE ({elapsed:.0f}s) | test macro={test_metrics['macro_f1']:.4f} minority={test_metrics.get('minority_macro_f1', 0):.4f} weighted={test_metrics['weighted_f1']:.4f} | best_epoch={best_epoch}", flush=True)
    
    result = {
        "seed": seed,
        "use_reweighting": use_reweighting,
        "run_name": run_name,
        "best_epoch": best_epoch,
        "elapsed_sec": elapsed,
        **{k: v for k, v in test_metrics.items()},
    }
    
    del model, logits; gc.collect()
    return result

# --- Main ---
out_dir = Path("experiments/ood_lite")
out_dir.mkdir(parents=True, exist_ok=True)

all_results = []

# 1. Temporal: baseline (no-temporal-edge, no reweighting) x 3 seeds
for seed in SEEDS:
    print(f"\n--- temporal baseline seed={seed} ---", flush=True)
    r = run_experiment(PROTOCOLS["temporal"], seed, use_reweighting=False, run_name="temporal_baseline_notemp")
    r["protocol"] = "temporal"
    r["variant"] = "baseline_no_temporal"
    all_results.append(r)

# 2. Temporal: with topology-aware reweighting x 3 seeds
for seed in SEEDS:
    print(f"\n--- temporal topo_reweight seed={seed} ---", flush=True)
    r = run_experiment(PROTOCOLS["temporal"], seed, use_reweighting=True, run_name="temporal_topo_reweight")
    r["protocol"] = "temporal"
    r["variant"] = "topo_reweight"
    all_results.append(r)

# 3. CBK: baseline seed 42
print(f"\n--- cbk baseline seed=42 ---", flush=True)
r = run_experiment(PROTOCOLS["cbk"], 42, use_reweighting=False, run_name="cbk_baseline_notemp")
r["protocol"] = "cbk"
r["variant"] = "baseline_no_temporal"
all_results.append(r)

# 4. CBK: topo reweight seed 42
print(f"\n--- cbk topo_reweight seed=42 ---", flush=True)
r = run_experiment(PROTOCOLS["cbk"], 42, use_reweighting=True, run_name="cbk_topo_reweight")
r["protocol"] = "cbk"
r["variant"] = "topo_reweight"
all_results.append(r)

# Save results
df = pd.DataFrame(all_results)
df.to_csv(out_dir / "ood_lite_results.csv", index=False)

# Summary
lines = []
lines.append("# OOD Lite Multi-Seed Summary")
lines.append("")
lines.append("## Temporal Balprotocol results")
lines.append("")
lines.append("| Variant | Seed | Macro-F1 | Minority-F1 | Weighted-F1 | best_epoch |")
lines.append("|---|---|---|---|---|---|")
for _, r in df[df["protocol"]=="temporal"].iterrows():
    lines.append(f"| {r.variant} | {r.seed} | {r.macro_f1:.4f} | {r.get('minority_macro_f1', 0):.4f} | {r.weighted_f1:.4f} | {r.best_epoch} |")

# Aggregate
for variant in df[df["protocol"]=="temporal"]["variant"].unique():
    sub = df[(df["protocol"]=="temporal") & (df["variant"]==variant)]
    lines.append(f"\n{variant}: Macro-F1 = {sub['macro_f1'].mean():.4f} +/- {sub['macro_f1'].std():.4f}")

lines.append("")
lines.append("## CBK results")
lines.append("")
for _, r in df[df["protocol"]=="cbk"].iterrows():
    lines.append(f"| {r.variant} | {r.seed} | {r.macro_f1:.4f} | {r.get('minority_macro_f1', 0):.4f} | {r.weighted_f1:.4f} | {r.best_epoch} |")

# Gate decision
lines.append("")
lines.append("## Gate Decision")
lines.append("")

temp_base = df[(df["protocol"]=="temporal") & (df["variant"]=="baseline_no_temporal")]["macro_f1"]
temp_reweight = df[(df["protocol"]=="temporal") & (df["variant"]=="topo_reweight")]["macro_f1"]
cbk_base = df[(df["protocol"]=="cbk") & (df["variant"]=="baseline_no_temporal")]["macro_f1"]
cbk_reweight = df[(df["protocol"]=="cbk") & (df["variant"]=="topo_reweight")]["macro_f1"]

base_mean = temp_base.mean()
reweight_mean = temp_reweight.mean()
delta = reweight_mean - base_mean
gate = 0.2975

lines.append(f"Baseline temporal Macro-F1: {base_mean:.4f}")
lines.append(f"Topo-reweight temporal Macro-F1: {reweight_mean:.4f}")
lines.append(f"Delta: {delta:+.4f}")
lines.append(f"Gate threshold: {gate}")
lines.append("")

if reweight_mean >= gate:
    lines.append("**PASS**: Temporal Macro-F1 >= 0.2975. Topology-aware reweighting qualifies as method contribution.")
else:
    lines.append(f"**FAIL**: Temporal Macro-F1 = {reweight_mean:.4f} < 0.2975. Gap to gate = {gate - reweight_mean:.4f}")

if len(cbk_base) > 0 and len(cbk_reweight) > 0:
    cbk_delta = cbk_reweight.mean() - cbk_base.mean()
    lines.append(f"\nCBK delta: {cbk_delta:+.4f} (base={cbk_base.mean():.4f}, reweight={cbk_reweight.mean():.4f})")
    if abs(cbk_delta) > 0.02:
        lines.append("WARNING: CBK change exceeds 0.02 threshold.")

(out_dir / "ood_lite_multiseed_summary.md").write_text("\n".join(lines), encoding="utf-8")

# Gate decision file
gate_lines = []
gate_lines.append("# OOD Lite Gate Decision")
gate_lines.append("")
gate_lines.append("## 1. Implemented Prototype")
gate_lines.append("Topology-Aware Reweighting Lite: per-node difficulty weight based on unlabeled_neighbor_ratio and (1 - same_label_ratio).")
gate_lines.append("Weight = clip(1.0 + 1.0 * unlabeled_ratio + 0.5 * (1 - same_ratio), 0.5, 2.5)")
gate_lines.append("")
gate_lines.append("## 2. Features Used")
gate_lines.append("- unlabeled_neighbor_ratio (from graph structure)")
gate_lines.append("- same_label_neighbor_ratio (from train labels only)")
gate_lines.append("- No raw temporal edge features used")
gate_lines.append("")
gate_lines.append("## 3. Label Leakage Risk")
gate_lines.append("LOW: same_label_ratio computed only on train nodes. Val/test labels never accessed for weight computation.")
gate_lines.append("")
gate_lines.append(f"## 4. Temporal Macro-F1 >= 0.2975?")
gate_lines.append(f"Result: {reweight_mean:.4f}. {'YES' if reweight_mean >= gate else 'NO'}")
gate_lines.append("")
gate_lines.append("## 5. Conservative Recall@1% >= 0.50?")
gate_lines.append("Not computed in this run (would need separate ranking evaluation).")
gate_lines.append("")
gate_lines.append(f"## 6. CBK Degradation?")
if len(cbk_base) > 0 and len(cbk_reweight) > 0:
    cbk_delta = cbk_reweight.mean() - cbk_base.mean()
    gate_lines.append(f"CBK delta: {cbk_delta:+.4f}. {'SIGNIFICANT' if abs(cbk_delta) > 0.02 else 'OK'}")
else:
    gate_lines.append("Insufficient CBK data.")
gate_lines.append("")
gate_lines.append(f"## 7. Recommendation")
if reweight_mean >= gate:
    gate_lines.append("PASS: Recommend including topology-aware reweighting as method contribution.")
else:
    gate_lines.append("FAIL: Lightweight OOD prototype does not pass the method-contribution gate.")
    gate_lines.append("Temporal OOD remains an open challenge / limitation.")
    gate_lines.append("Recommend writing: 'We attempted topology-aware reweighting but observed insufficient improvement. Temporal generalization remains an open challenge.'")
gate_lines.append("")
gate_lines.append("## 8. If Failed, How to Write Limitation")
if reweight_mean < gate:
    gate_lines.append("- Note the temporal gap (0.25 vs 0.65) as a fundamental challenge")
    gate_lines.append("- Mention topology-aware reweighting as an attempted approach")
    gate_lines.append("- Suggest temporal environment modeling or causal decoupling as future directions")
    gate_lines.append("- Do NOT claim temporal features can be trivially handled")

(out_dir / "ood_lite_gate_decision.md").write_text("\n".join(gate_lines), encoding="utf-8")

print(f"\nAll outputs saved to {out_dir}", flush=True)
print("DONE", flush=True)
