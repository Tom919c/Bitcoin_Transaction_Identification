"""Verify key experiments can be re-run. Smoke test with --smoke flag.
Usage: python scripts/verify_experiments.py [--smoke] [--dataset DATASET]
"""
import subprocess, sys, os, argparse

WD = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
PYTHON = r"D:\Software\Anaconda\envs\MCM\python.exe"

KEY_EXPERIMENTS = [
    {
        "name": "CBK MLP seed42",
        "cmd": [PYTHON, "scripts/run_benchmark.py",
                "--data", "data/processed/protocols/class_balanced_khop.pt",
                "--models", "mlp", "--seed", "42", "--run-name", "verify_mlp"],
        "expected_macro_f1_range": (0.38, 0.43),
    },
    {
        "name": "CBK SAGE seed42",
        "cmd": [PYTHON, "scripts/run_benchmark.py",
                "--data", "data/processed/protocols/class_balanced_khop.pt",
                "--models", "sage", "--seed", "42", "--run-name", "verify_sage"],
        "expected_macro_f1_range": (0.55, 0.62),
    },
    {
        "name": "CBK EGS seed42",
        "cmd": [PYTHON, "scripts/run_benchmark.py",
                "--data", "data/processed/protocols/class_balanced_khop.pt",
                "--models", "edge_gated_sage", "--seed", "42", "--run-name", "verify_egs"],
        "expected_macro_f1_range": (0.60, 0.68),
    },
    {
        "name": "Temporal EGS seed42",
        "cmd": [PYTHON, "scripts/run_benchmark.py",
                "--data", "data/processed/protocols/temporal_balanced.pt",
                "--models", "edge_gated_sage", "--seed", "42", "--run-name", "verify_temporal"],
        "expected_macro_f1_range": (0.22, 0.30),
    },
    {
        "name": "OOD single (temp_base_s42)",
        "cmd": [PYTHON, "scripts/run_ood_single.py",
                "--data", "data/processed/protocols/temporal_balanced.pt",
                "--seed", "42", "--name", "verify_ood",
                "--logdir", "experiments/ood_lite", "--patience", "40"],
        "expected_macro_f1_range": (0.20, 0.28),
    },
]

ap = argparse.ArgumentParser()
ap.add_argument("--smoke", action="store_true", help="Add --smoke flag to benchmark commands")
ap.add_argument("--dataset", default=None, help="Only run experiments for this dataset keyword")
ap.add_argument("--dry-run", action="store_true", help="Only print commands, don't execute")
args = ap.parse_args()

for exp in KEY_EXPERIMENTS:
    if args.dataset and args.dataset.lower() not in exp["name"].lower():
        continue
    cmd = list(exp["cmd"])
    if args.smoke and "run_benchmark.py" in cmd[1]:
        cmd.append("--smoke")
    if args.dry_run:
        print(f"[DRY RUN] {exp['name']}: {' '.join(cmd)}")
        continue
    print(f"\n=== {exp['name']} ===")
    print(f"  cmd: {' '.join(cmd[1:])}")
    proc = subprocess.run(cmd, cwd=WD, capture_output=True, text=True, timeout=3600)
    if proc.returncode == 0:
        print(f"  PASS (rc=0)")
    else:
        print(f"  FAIL (rc={proc.returncode})")
        if proc.stderr:
            print(f"  stderr: {proc.stderr[:200]}")

print("\n=== Verification complete ===")
