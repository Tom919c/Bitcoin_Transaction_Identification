"""Single OOD experiment with checkpoint resume support.
Args: --data PATH --seed INT --reweight --name NAME --logdir DIR --patience N
Saves checkpoint every 10 epochs. Resumes from checkpoint if found."""
import sys, os, time, argparse, json, torch, numpy as np
WD = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
sys.path.insert(0, os.path.join(WD, "src"))
os.chdir(WD)
os.environ["PYTHONUNBUFFERED"] = "1"

from btcaml.data.label_maps import RAW_LABELS_11, UNKNOWN_LABEL
from btcaml.models.registry import build_model
from btcaml.utils.seed import seed_everything
from btcaml.evaluation.metrics import classification_metrics
import torch.nn.functional as F

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--reweight", action="store_true")
ap.add_argument("--name", required=True)
ap.add_argument("--logdir", required=True)
ap.add_argument("--patience", type=int, default=40)
args = ap.parse_args()

CKPT_PATH = os.path.join(args.logdir, "ckpt_" + args.name + ".pt")
RESULT_PATH = os.path.join(args.logdir, "RESULT_" + args.name + ".json")

# Skip if already done
if os.path.exists(RESULT_PATH):
    print(f"=== {args.name} already done, skipping ===", flush=True)
    sys.exit(0)

print(f"=== {args.name} seed={args.seed} reweight={args.reweight} ===", flush=True)
seed_everything(args.seed)

payload = torch.load(args.data, map_location="cpu", weights_only=False)
data = payload["data"] if isinstance(payload, dict) and "data" in payload else payload
x, ei, y = data.x, data.edge_index, data.y
ea = data.edge_attr.clone() if hasattr(data, "edge_attr") and data.edge_attr is not None else None
if ea is not None:
    for c in [0, 1, 6, 7, 8]:
        if c < ea.shape[1]: ea[:, c] = 0.0

tm = data.train_mask.bool() & (y != UNKNOWN_LABEL)
vm = data.val_mask.bool() & (y != UNKNOWN_LABEL)
tsm = data.test_mask.bool() & (y != UNKNOWN_LABEL)
edge_dim = ea.shape[1] if ea is not None else None

model = build_model("edge_gated_sage", int(x.shape[1]), 11, edge_dim=edge_dim,
    params={"hidden_channels": 128, "num_layers": 3, "dropout": 0.3, "edge_hidden": 64, "use_direction": True})
opt = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=5e-4)

ty = y[tm]; cc = torch.bincount(ty, minlength=11).float().clamp(min=1)
cw = (1.0 / cc); cw = cw / cw.mean(); cw = cw.clamp(max=10.0)

# Topology-aware weights
tw = None
if args.reweight:
    src_arr, dst_arr = ei[0].numpy(), ei[1].numpy()
    n = len(y)
    in_nb = [[] for _ in range(n)]; out_nb = [[] for _ in range(n)]
    for s, d in zip(src_arr, dst_arr):
        out_nb[s].append(d); in_nb[d].append(s)
    tidx = torch.where(tm)[0].numpy()
    tw = np.ones(len(tidx), dtype=np.float32)
    for i, nid in enumerate(tidx):
        tl = y[nid]; all_n = in_nb[nid] + out_nb[nid]
        if not all_n: continue
        lab = [y[nb] for nb in all_n if y[nb] != -1]
        unr = (len(all_n) - len(lab)) / max(len(all_n), 1)
        sr = sum(1 for l in lab if l == tl) / max(len(lab), 1)
        tw[i] = np.clip(1.0 + 1.0 * unr + 0.5 * (1 - sr), 0.5, 2.5)
    tw = torch.tensor(tw, dtype=torch.float32)
    print("Topo weights: min=%.3f max=%.3f mean=%.3f" % (tw.min(), tw.max(), tw.mean()), flush=True)

# Resume from checkpoint if exists
start_epoch = 1
bm, bs, be, pat = -1, None, -1, 0
elapsed_so_far = 0

if os.path.exists(CKPT_PATH):
    ckpt = torch.load(CKPT_PATH, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state"])
    opt.load_state_dict(ckpt["opt_state"])
    start_epoch = ckpt["epoch"] + 1
    bm = ckpt["best_val_f1"]
    be = ckpt["best_epoch"]
    pat = ckpt["patience_counter"]
    bs = {k: v.clone() for k, v in ckpt["best_model_state"].items()}
    elapsed_so_far = ckpt.get("elapsed_so_far", 0)
    print(f"[RESUME] from epoch {start_epoch}, best={bm:.4f} @ {be}, pat={pat}", flush=True)

t0 = time.time()
for ep in range(start_epoch, 201):
    model.train(); opt.zero_grad()
    logits = model(x, ei, ea)
    pl = F.cross_entropy(logits[tm], y[tm], weight=cw, reduction="none")
    if tw is not None: pl = pl * tw
    loss = pl.mean(); loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
    model.eval()
    with torch.no_grad():
        vl = model(x, ei, ea)
        vm2 = classification_metrics(vl, y, vm, RAW_LABELS_11)
    vf = vm2.get("macro_f1", 0)
    if vf > bm:
        bm = vf; bs = {k: v.clone() for k, v in model.state_dict().items()}; be = ep; pat = 0
    else:
        pat += 1
    if pat >= args.patience:
        print("epoch %04d | early_stop best=%.4f @ %d" % (ep, bm, be), flush=True); break
    if ep % 10 == 0 or ep == 1:
        print("epoch %04d | loss=%.4f val=%.4f best=%.4f [%ds]" % (ep, loss.item(), vf, bm, int(elapsed_so_far + time.time()-t0)), flush=True)
    # Save checkpoint every 10 epochs
    if ep % 10 == 0:
        torch.save({
            "epoch": ep, "model_state": model.state_dict(), "opt_state": opt.state_dict(),
            "best_val_f1": bm, "best_epoch": be, "best_model_state": bs,
            "patience_counter": pat, "elapsed_so_far": elapsed_so_far + time.time() - t0,
        }, CKPT_PATH)

# Final evaluation
model.load_state_dict(bs); model.eval()
with torch.no_grad(): tl = model(x, ei, ea)
tm2 = classification_metrics(tl, y, tsm, RAW_LABELS_11)
elapsed = elapsed_so_far + time.time() - t0

r = {"seed": args.seed, "macro_f1": tm2["macro_f1"], "minority_macro_f1": tm2.get("minority_macro_f1", 0),
     "weighted_f1": tm2["weighted_f1"], "best_epoch": be, "elapsed_s": int(elapsed),
     "variant": "topo_reweight" if args.reweight else "baseline_no_temporal"}
print("RESULT|%.6f|%.6f|%.6f|%d|%.0fs" % (tm2["macro_f1"], tm2.get("minority_macro_f1",0), tm2["weighted_f1"], be, elapsed), flush=True)
with open(RESULT_PATH, "w") as f:
    json.dump(r, f)
# Clean up checkpoint
if os.path.exists(CKPT_PATH):
    os.remove(CKPT_PATH)
