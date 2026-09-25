#!/bin/bash
# Run a frozen Gate 3A evaluation pair (run01 + run02), sequentially, on the lab server.
#
# WHY ON THE SERVER, AND WHY BOTH RUNS ON ONE HOST
#   The evaluation JSON embeds `environment = {python, sqlite}` and computes
#   `secondary.variation_of_information` with math.log. Two runs on different hosts cannot be
#   byte-identical across interpreter/libm implementations, so the finalizer's hash-concordance
#   check cannot pass. Both authoritative runs must therefore execute on the same machine, with
#   identical frozen runner bytes and hash-verified inputs.
#
# WHY SEQUENTIAL
#   The protocol requires two consecutive independent runs, not two concurrent ones.
#
# WHY THE RUNNER WRITES NOTHING UNTIL IT FINISHES
#   There is no progress log and no partial output. A run that is killed or stalls cannot be
#   resumed -- it must restart from scratch. Budget for the full duration or don't start.
#
# USAGE
#   Edit the variables below, then launch detached:
#       setsid nohup ./run_frozen_s0_pair.sh > pair.out 2>&1 < /dev/null
#
#   IMPORTANT -- DO NOT append `& sleep N` to the launch command over ssh. The sandbox sends
#   SIGTERM to such compound commands (exit 1, no output) WHILE THE SERVER-SIDE PROCESS IS
#   ALREADY RUNNING. Repeated "failed" launches therefore accumulate MULTIPLE CONCURRENT
#   INSTANCES that fight over the same state DB and write the same output file. Launch, return
#   immediately, then verify with a SEPARATE command using `pgrep -cf` (count, not `head -3`).
set -u

cd /workspace/chenquan/asof-entity-graph
export UV_PYTHON_INSTALL_DIR=/workspace/chenquan/toolchain/uv-python
export UV_CACHE_DIR=/workspace/chenquan/toolchain/uv-cache
UV=/workspace/chenquan/toolchain/uv

SUMMARY=experiments/diagnostics/aws_btc_s0_union_extract_v1_1_20260911/summary.json
STATE_DB=data/raw/aws_btc_prefix_v0_1_20260910/s0_state/s0_union_v1_1.sqlite
RUNNER=scripts/research/evaluate_aws_btc_s0.py
# Output directory prefix; the script appends _run01 / _run02.
BASE=experiments/diagnostics/aws_btc_s0_structure_eval_v1_3_20260924_server
LOG=/workspace/chenquan/s0_pair.log

log() { echo "[$(date '+%F %T')] $*" >>"$LOG"; }

log "pair start (runner=$(sha256sum "$RUNNER" | cut -d' ' -f1))"
for n in 01 02; do
  OUTDIR="${BASE}_run${n}"
  if [ -f "$OUTDIR/evaluation.json" ]; then
    log "run${n}: output already exists, skipping"
    continue
  fi
  mkdir -p "$OUTDIR"
  log "run${n}: start"
  set +e
  "$UV" run python "$RUNNER" --summary "$SUMMARY" --state-db "$STATE_DB" \
       --output "$OUTDIR/evaluation.json" >>"$OUTDIR/run.log" 2>&1
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    log "run${n}: done sha256=$(sha256sum "$OUTDIR/evaluation.json" | cut -d' ' -f1)"
  else
    log "run${n}: FAILED (exit $rc)"
    exit 1
  fi
done
log "pair done"

# EXPECTED DURATIONS, MEASURED (lab server, mechanical /dev/sdb, quiet machine)
#   run01: 1h15m43s   -- fast because it followed the 21 GB state-DB transfer and the file was
#                        still in page cache
#   run02: 7h18m32s   -- cold cache, 4 KB random reads, mechanical seek-bound
# A cold-cache run can be ~6x slower than a warm-cache one and still be byte-identical. Do NOT
# extrapolate completion time from a short sample taken in the first few minutes of a run: the
# startup phase is index warm-up and looks far slower than steady state.
