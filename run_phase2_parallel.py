"""Parallel experiment runner using multiprocessing within a single foreground process."""
import subprocess, sys, time, os, json, threading
from datetime import datetime
from pathlib import Path
from multiprocessing import Process, Queue

WD = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
PYTHON = r"D:\Software\Anaconda\envs\MCM\python.exe"
LOGDIR = Path(WD) / "experiments" / "logs" / "phase2_rerun"
LOGDIR.mkdir(parents=True, exist_ok=True)

def run_one(name, args, result_queue):
    """Run a single experiment, log output, put result in queue."""
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
        for raw_line in iter(proc.stdout.readline, b""):
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            elapsed = time.time() - start_time
            try:
                print(f"  [{name}][{elapsed:.0f}s] {line}", flush=True)
            except UnicodeEncodeError:
                print(f"  [{name}][{elapsed:.0f}s] {line.encode('ascii',errors='replace').decode()}", flush=True)
            log_f.write(line + "\n")
            log_f.flush()
        proc.wait()
        elapsed = time.time() - start_time
        result_queue.put((name, proc.returncode, elapsed))

def progress_monitor(procs, interval=300):
    """Periodically report which processes are still alive."""
    while any(p.is_alive() for p in procs):
        time.sleep(interval)
        alive = [p.name for p in procs if p.is_alive()]
        try:
            print(f"\n[MONITOR {datetime.now():%H:%M:%S}] Still running: {', '.join(alive)}", flush=True)
        except UnicodeEncodeError:
            print(f"\n[MONITOR {datetime.now():%H:%M:%S}] Still running: {len(alive)} processes", flush=True)
        # Check log file sizes
        for name in ["cbk_no_temporal", "temporal_s43", "temporal_s44"]:
            lp = LOGDIR / f"{name}_output.log"
            if lp.exists():
                sz = lp.stat().st_size
                try:
                    print(f"  {name}_output.log: {sz} bytes", flush=True)
                except UnicodeEncodeError:
                    pass

EXPERIMENTS = [
    ("cbk_no_temporal", [
        "scripts/run_benchmark.py", "--data", "data/processed/protocols/class_balanced_khop_no_temporal.pt",
        "--models", "edge_gated_sage", "--device", "cpu", "--epochs", "200",
        "--early-stopping-patience", "50", "--seed", "42", "--loss", "weighted_ce",
        "--run-name", "cbk_no_temporal_egs_r3"
    ]),
    ("temporal_s43", [
        "scripts/run_benchmark.py", "--data", "data/processed/protocols/temporal_balanced.pt",
        "--models", "edge_gated_sage", "--device", "cpu", "--epochs", "200",
        "--early-stopping-patience", "50", "--seed", "43", "--loss", "weighted_ce",
        "--run-name", "temporal_egs_s43_r3"
    ]),
    ("temporal_s44", [
        "scripts/run_benchmark.py", "--data", "data/processed/protocols/temporal_balanced.pt",
        "--models", "edge_gated_sage", "--device", "cpu", "--epochs", "200",
        "--early-stopping-patience", "50", "--seed", "44", "--loss", "weighted_ce",
        "--run-name", "temporal_egs_s44_r3"
    ]),
]

if __name__ == "__main__":
    try:
        print(f"=== Parallel Experiment Runner [{datetime.now():%Y-%m-%d %H:%M:%S}] ===", flush=True)
        print(f"Running {len(EXPERIMENTS)} experiments IN PARALLEL", flush=True)
        
        result_queue = Queue()
        procs = []
        for name, args in EXPERIMENTS:
            p = Process(target=run_one, args=(name, args, result_queue), name=name, daemon=False)
            procs.append(p)
        
        # Start monitor thread
        monitor = threading.Thread(target=progress_monitor, args=(procs, 300), daemon=True)
        monitor.start()
        
        # Start all experiments
        for p in procs:
            p.start()
            try:
                print(f"Started {p.name} (PID {p.pid})", flush=True)
            except UnicodeEncodeError:
                print(f"Started process PID {p.pid}", flush=True)
        
        # Wait for all to finish
        for p in procs:
            p.join()
        
        # Collect results
        results = {}
        while not result_queue.empty():
            name, rc, elapsed = result_queue.get_nowait()
            results[name] = (rc, elapsed)
        
        print(f"\n{'='*60}", flush=True)
        print(f"ALL EXPERIMENTS COMPLETE [{datetime.now():%Y-%m-%d %H:%M:%S}]", flush=True)
        for name in ["cbk_no_temporal", "temporal_s43", "temporal_s44"]:
            if name in results:
                rc, elapsed = results[name]
                status = "OK" if rc == 0 else f"FAIL(code={rc})"
                print(f"  {name}: {status} ({elapsed:.0f}s)", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback; traceback.print_exc()
