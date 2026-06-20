"""OOD Lite sequential runner - loads data once per protocol, runs all seeds/variants."""
import sys, os, gc, time, json
ROOT = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["PYTHONUNBUFFERED"] = "1"

import torch, numpy as np, pandas as pd
from pathlib import Path
from btcaml.data.label_maps import RAW_LABELS_11, UNKNOWN_LABEL
from btcaml.models.registry import build_model
from btcaml.utils.seed import seed_everything
from btcaml.evaluation.metrics import classification_metrics

EPOCHS = 200; PATIENCE = 50; NUM_CLASSES = 11
PARAMS = {"hidden_channels": 128, "num_layers": 3, "dropout": 0.3, "edge_hidden": 64, "use_direction": True}

def compute_topo_weights(data, train_mask):
    y = data.y.numpy(); ei = data.edge_index.numpy()
    src, dst = ei[0], ei[1]; n = len(y)
    in_nb = [[] for _ in range(n)]; out_nb = [[] for _ in range(n)]
    for s, d in zip(src, dst): out_nb[s].append(d); in_nb[d].append(s)
    tidx = torch.where(train_mask)[0].numpy()
    w = np.ones(len(tidx), dtype=np.float32)
    for i, nid in enumerate(tidx):
        tl = y[nid]; all_n = in_nb[nid] + out_nb[nid]
        if not all_n: continue
        lab = [y[nb] for nb in all_n if y[nb] != -1]
        unr = (len(all_n) - len(lab)) / max(len(all_n), 1)
        sr = sum(1 for l in lab if l == tl) / max(len(lab), 1)
        w[i] = np.clip(1.0 + 1.0*unr + 0.5*(1-sr), 0.5, 2.5)
    return torch.tensor(w, dtype=torch.float32)

def train_eval(x, ei, ea, y, train_mask, val_mask, test_mask, seed, topo_w):
    seed_everything(seed)
    edge_dim = ea.shape[1] if ea is not None else None
    model = build_model("edge_gated_sage", int(x.shape[1]), NUM_CLASSES, edge_dim=edge_dim, params=dict(PARAMS))
    opt = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=5e-4)
    ty = y[train_mask]; cc = torch.bincount(ty, minlength=NUM_CLASSES).float().clamp(min=1)
    cw = (1.0/cc); cw = cw/cw.mean(); cw = cw.clamp(max=10.0)
    best_m, best_s, best_e, pat = -1, None, -1, 0
    t0 = time.time()
    for ep in range(1, EPOCHS+1):
        model.train(); opt.zero_grad()
        logits = model(x, ei, ea)
        pl = torch.nn.functional.cross_entropy(logits[train_mask], y[train_mask], weight=cw, reduction="none")
        if topo_w is not None: pl = pl * topo_w
        loss = pl.mean(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        model.eval()
        with torch.no_grad():
            vl = model(x, ei, ea)
            vm = classification_metrics(vl, y, val_mask, RAW_LABELS_11)
        vf = vm.get("macro_f1", 0)
        if vf > best_m: best_m=vf; best_s={k:v.clone() for k,v in model.state_dict().items()}; best_e=ep; pat=0
        else: pat += 1
        if pat >= PATIENCE: print(f"    Early stop {ep}, best={best_m:.4f}@{best_e}", flush=True); break
        if ep % 50 == 0 or ep == 1: print(f"    ep {ep:04d} loss={loss.item():.4f} val={vf:.4f} best={best_m:.4f} [{time.time()-t0:.0f}s]", flush=True)
    model.load_state_dict(best_s); model.eval()
    with torch.no_grad(): tl = model(x, ei, ea)
    tm = classification_metrics(tl, y, test_mask, RAW_LABELS_11)
    elapsed = time.time() - t0
    print(f"    DONE macro={tm['macro_f1']:.4f} minority={tm.get('minority_macro_f1',0):.4f} weighted={tm['weighted_f1']:.4f} best_ep={best_e} [{elapsed:.0f}s]", flush=True)
    del model; gc.collect()
    return {"seed": seed, "macro_f1": tm["macro_f1"], "minority_macro_f1": tm.get("minority_macro_f1", 0),
            "weighted_f1": tm["weighted_f1"], "best_epoch": best_e, "elapsed": elapsed, **{f"class_{i}_f1": tm.get(f"{RAW_LABELS_11[i]}_f1", 0) for i in range(NUM_CLASSES)}}

PROTOCOLS = {
    "temporal": "data/processed/protocols/temporal_balanced.pt",
    "cbk": "data/processed/protocols/class_balanced_khop.pt",
}
SEEDS = [42, 43, 44]
all_results = []
out_dir = Path("experiments/ood_lite"); out_dir.mkdir(parents=True, exist_ok=True)

for proto_name, proto_path in PROTOCOLS.items():
    seeds = SEEDS if proto_name == "temporal" else [42]
    print(f"\n{'='*60}", flush=True)
    print(f"Loading {proto_name}...", flush=True)
    payload = torch.load(proto_path, map_location="cpu", weights_only=False)
    data = payload["data"] if isinstance(payload, dict) and "data" in payload else payload
    x, ei = data.x, data.edge_index
    ea_raw = data.edge_attr if hasattr(data, "edge_attr") else None
    # Zero temporal features
    if ea_raw is not None:
        ea = ea_raw.clone()
        for c in [0, 1, 6, 7, 8]:
            if c < ea.shape[1]: ea[:, c] = 0.0
    else: ea = None
    y = data.y
    tm = data.train_mask.bool() & (y != UNKNOWN_LABEL)
    vm = data.val_mask.bool() & (y != UNKNOWN_LABEL)
    testm = data.test_mask.bool() & (y != UNKNOWN_LABEL)
    
    topo_w = compute_topo_weights(data, tm)
    print(f"Topo weights: min={topo_w.min():.3f} max={topo_w.max():.3f} mean={topo_w.mean():.3f}", flush=True)
    
    for seed in seeds:
        # Baseline (no reweighting)
        print(f"\n--- {proto_name} baseline seed={seed} ---", flush=True)
        r = train_eval(x, ei, ea, y, tm, vm, testm, seed, topo_w=None)
        r.update({"protocol": proto_name, "variant": "baseline_no_temporal"})
        all_results.append(r)
        gc.collect()
        
        # Topo reweight
        print(f"\n--- {proto_name} topo_reweight seed={seed} ---", flush=True)
        r = train_eval(x, ei, ea, y, tm, vm, testm, seed, topo_w=topo_w)
        r.update({"protocol": proto_name, "variant": "topo_reweight"})
        all_results.append(r)
        gc.collect()
    
    del data, x, ei, ea, y, tm, vm, testm, topo_w; gc.collect()

df = pd.DataFrame(all_results)
df.to_csv(out_dir / "ood_lite_results.csv", index=False)
print(f"\nResults saved to {out_dir / 'ood_lite_results.csv'}", flush=True)

# Summary + gate decision
lines = ["# OOD Lite Multi-Seed Summary", ""]
for proto in ["temporal", "cbk"]:
    sub = df[df["protocol"]==proto]
    lines.append(f"## {proto}")
    lines.append("")
    lines.append("| Variant | Seed | Macro-F1 | Minority-F1 | Weighted-F1 |")
    lines.append("|---|---|---|---|---|")
    for _, r in sub.iterrows():
        lines.append(f"| {r.variant} | {r.seed} | {r.macro_f1:.4f} | {r.minority_macro_f1:.4f} | {r.weighted_f1:.4f} |")
    for v in sub["variant"].unique():
        sv = sub[sub["variant"]==v]["macro_f1"]
        lines.append(f"\n{v}: {sv.mean():.4f} +/- {sv.std():.4f}")
    lines.append("")

tb = df[(df["protocol"]=="temporal")&(df["variant"]=="baseline_no_temporal")]["macro_f1"].mean()
tr = df[(df["protocol"]=="temporal")&(df["variant"]=="topo_reweight")]["macro_f1"].mean()
cb = df[(df["protocol"]=="cbk")&(df["variant"]=="baseline_no_temporal")]["macro_f1"].mean()
cr = df[(df["protocol"]=="cbk")&(df["variant"]=="topo_reweight")]["macro_f1"].mean()
delta = tr - tb; gate = 0.2975
lines.append("## Gate Decision")
lines.append(f"Temporal baseline: {tb:.4f}")
lines.append(f"Temporal reweight: {tr:.4f}")
lines.append(f"Delta: {delta:+.4f}")
lines.append(f"Gate: {gate}")
lines.append(f"CBK baseline: {cb:.4f}, reweight: {cr:.4f}, delta: {cr-cb:+.4f}")
lines.append("")
if tr >= gate:
    lines.append("**PASS**: Temporal >= 0.2975. Topology-aware reweighting qualifies.")
else:
    lines.append(f"**FAIL**: Temporal = {tr:.4f} < 0.2975. Gap = {gate-tr:.4f}")
    lines.append("Lightweight OOD prototype does not pass the method-contribution gate.")
    lines.append("Temporal OOD remains an open challenge / limitation.")
(out_dir / "ood_lite_multiseed_summary.md").write_text("\n".join(lines), encoding="utf-8")

# Gate decision file
gl = ["# OOD Lite Gate Decision", ""]
gl.append("## 1. Prototype: Topology-Aware Reweighting Lite")
gl.append("Weight = clip(1 + unlabeled_ratio + 0.5*(1-same_ratio), 0.5, 2.5)")
gl.append("## 2. Features: graph topology only (no temporal edge features)")
gl.append("## 3. Label Leakage: LOW (train-only)")
gl.append(f"## 4. Temporal Macro-F1 >= 0.2975? {tr:.4f} -> {'YES' if tr>=gate else 'NO'}")
gl.append(f"## 5. CBK Degradation? delta={cr-cb:+.4f} -> {'SIGNIFICANT' if abs(cr-cb)>0.02 else 'OK'}")
gl.append("## 6. Recommendation")
if tr >= gate:
    gl.append("PASS: Include as method contribution.")
else:
    gl.append("FAIL: Does not pass gate. Write as limitation.")
    gl.append("Suggested text: 'We attempted topology-aware reweighting but observed insufficient improvement. Temporal generalization remains an open challenge.'")
(out_dir / "ood_lite_gate_decision.md").write_text("\n".join(gl), encoding="utf-8")
print("\nAll outputs saved.", flush=True)
