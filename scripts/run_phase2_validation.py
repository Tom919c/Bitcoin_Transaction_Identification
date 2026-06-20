"""Phase 2: Route validation experiments on temporal_balanced.

Runs ablations and lightweight OOD prototypes.
"""
import subprocess
import sys
import os
import time

os.chdir(r"D:\Code\VSCode\Bitcoin_Transaction_Identification")
SCRIPT = "scripts/run_benchmark.py"
DATA = "data/processed/protocols/temporal_balanced.pt"
SEEDS = ["42"]

# Experiment definitions: (model, extra_args, run_name, description)
experiments = [
    # Already done - just for reference
    # ("mlp", [], "temporal_mlp_s42", "MLP baseline"),
    # ("sage", [], "temporal_sage_s42", "SAGE baseline"),
    # ("edge_gated_sage", [], "temporal_egs_s42", "EGS full"),
    # ("edge_gated_sage", ["--config", "configs/experiment/ablation_egs_no_direction.yaml"], "temporal_egs_no_dir", "EGS no direction"),

    # New experiments
    ("sage", [], "temporal_sage_s42_rerun", "SAGE baseline rerun"),
    ("edge_gated_sage", [], "temporal_egs_s42_rerun", "EGS full rerun"),
]

def run_exp(model, extra_args, run_name, desc):
    cmd = [sys.executable, SCRIPT,
        "--data", DATA,
        "--models", model,
        "--device", "cpu",
        "--epochs", "200",
        "--early-stopping-patience", "50",
        "--seed", "42",
        "--loss", "weighted_ce",
        "--run-name", run_name,
    ] + extra_args
    
    print("[START] {} | {}".format(run_name, desc), flush=True)
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = int(time.time() - t0)
    
    # Extract result
    for line in (result.stdout + result.stderr).split("\n"):
        if "test macro=" in line:
            print("[DONE] {} | {}s | {}".format(run_name, elapsed, line.strip()), flush=True)
            return
    
    print("[DONE] {} | {}s | no test result found".format(run_name, elapsed), flush=True)
    if result.returncode != 0:
        print("  STDERR:", result.stderr[-500:] if result.stderr else "empty", flush=True)

for model, extra, run_name, desc in experiments:
    run_exp(model, extra, run_name, desc)

print("\n=== All Phase 2 experiments complete ===", flush=True)
