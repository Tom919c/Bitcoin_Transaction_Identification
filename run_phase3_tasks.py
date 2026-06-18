import subprocess, sys, time, os, threading
from datetime import datetime
from multiprocessing import Process, Queue

WD = r"D:\Code\VSCode\Bitcoin_Transaction_Identification"
PYTHON = r"D:\Software\Anaconda\envs\MCM\python.exe"
LOGDIR = os.path.join(WD, "experiments", "logs", "phase3_tasks")
os.makedirs(LOGDIR, exist_ok=True)

def run_one(name, script, result_queue):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    log_path = os.path.join(LOGDIR, f"{name}.log")
    with open(log_path, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen([PYTHON, "-u", script], cwd=WD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, bufsize=0)
        start = time.time()
        for raw in iter(proc.stdout.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip()
            elapsed = time.time() - start
            try:
                print(f"  [{name}][{elapsed:.0f}s] {line}", flush=True)
            except UnicodeEncodeError:
                print(f"  [{name}][{elapsed:.0f}s] {line.encode('ascii',errors='replace').decode()}", flush=True)
            lf.write(line + "\n"); lf.flush()
        proc.wait()
        elapsed = time.time() - start
        result_queue.put((name, proc.returncode, elapsed))

def monitor(procs, interval=120):
    while any(p.is_alive() for p in procs):
        time.sleep(interval)
        alive = [p.name for p in procs if p.is_alive()]
        try:
            print(f"\n[MONITOR {datetime.now():%H:%M:%S}] Running: {alive}", flush=True)
        except:
            pass

TASKS = [
    ("task_a", "scripts/task_a_ranking.py"),
    ("task_b", "scripts/task_b_temporal_analysis.py"),
    ("task_c", "scripts/task_c_confusion_study.py"),
]

if __name__ == "__main__":
    print(f"=== Phase 3 Tasks [{datetime.now():%Y-%m-%d %H:%M:%S}] ===", flush=True)
    print(f"Running {len(TASKS)} tasks IN PARALLEL", flush=True)
    rq = Queue()
    procs = []
    for name, script in TASKS:
        p = Process(target=run_one, args=(name, script, rq), name=name, daemon=False)
        procs.append(p)
    mon = threading.Thread(target=monitor, args=(procs, 120), daemon=True)
    mon.start()
    for p in procs:
        p.start()
        try:
            print(f"Started {p.name} (PID {p.pid})", flush=True)
        except:
            pass
    for p in procs:
        p.join()
    results = {}
    while not rq.empty():
        n, rc, el = rq.get_nowait()
        results[n] = (rc, el)
    print(f"\n{'='*60}", flush=True)
    print(f"ALL TASKS COMPLETE [{datetime.now():%Y-%m-%d %H:%M:%S}]", flush=True)
    for name, _ in TASKS:
        if name in results:
            rc, el = results[name]
            print(f"  {name}: {'OK' if rc==0 else f'FAIL({rc})'} ({el:.0f}s)", flush=True)
