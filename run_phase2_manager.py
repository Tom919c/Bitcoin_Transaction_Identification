import subprocess, sys, time, os, json
from datetime import datetime
from pathlib import Path

WD = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
PYTHON = r"D:\Software\Anaconda\envs\MCM\python.exe"
LOGDIR = Path(WD) / "experiments" / "logs" / "phase2_rerun"
LOGDIR.mkdir(parents=True, exist_ok=True)

EXPERIMENTS = [
    ("cbk_no_temporal", [
        "scripts/run_benchmark.py", "--data", "data/processed/protocols/class_balanced_khop_no_temporal.pt",
        "--models", "edge_gated_sage", "--device", "cpu", "--epochs", "200",
        "--early-stopping-patience", "50", "--seed", "42", "--loss", "weighted_ce",
        "--run-name", "cbk_no_temporal_egs_r2"
    ]),
    ("temporal_s43", [
        "scripts/run_benchmark.py", "--data", "data/processed/protocols/temporal_balanced.pt",
        "--models", "edge_gated_sage", "--device", "cpu", "--epochs", "200",
        "--early-stopping-patience", "50", "--seed", "43", "--loss", "weighted_ce",
        "--run-name", "temporal_egs_s43_r2"
    ]),
    ("temporal_s44", [
        "scripts/run_benchmark.py", "--data", "data/processed/protocols/temporal_balanced.pt",
        "--models", "edge_gated_sage", "--device", "cpu", "--epochs", "200",
        "--early-stopping-patience", "50", "--seed", "44", "--loss", "weighted_ce",
        "--run-name", "temporal_egs_s44_r2"
    ]),
]

def safe_print(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"), flush=True)

def run_experiment(name, args):
    safe_print(f"\n{'='*60}")
    safe_print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] STARTING: {name}")
    safe_print(f"{'='*60}")
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    log_path = LOGDIR / f"{name}_output.log"
    with open(log_path, "w", encoding="utf-8") as log_f:
        proc = subprocess.Popen(
            [PYTHON, "-u"] + args,
            cwd=WD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, bufsize=0
        )
        
        start_time = time.time()
        for raw_line in iter(proc.stdout.readline, b''):
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            elapsed = time.time() - start_time
            safe_print(f"  [{elapsed:.0f}s] {line}")
            log_f.write(line + "\n")
            log_f.flush()
        
        proc.wait()
        elapsed = time.time() - start_time
        status = "SUCCESS" if proc.returncode == 0 else f"FAILED(code={proc.returncode})"
        safe_print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] {status}: {name} (took {elapsed:.0f}s)")
        return proc.returncode

results = {}
for name, args in EXPERIMENTS:
    rc = run_experiment(name, args)
    results[name] = rc

safe_print(f"\n{'='*60}")
safe_print("ALL EXPERIMENTS COMPLETE")
for name, rc in results.items():
    safe_print(f"  {name}: {'OK' if rc == 0 else f'FAIL({rc})'}")
