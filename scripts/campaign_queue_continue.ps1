# Sprint-1 continuation queue: runs AFTER the main 13-step queue ends.
# 1) Formal 3-seed x 200-epoch runs of the screen winner (read from winner_decision.txt)
# 2) Single pre-registered test opening for E0 / winner / Dir-SAGE checkpoints
# Usage: powershell -NoProfile -File scripts/campaign_queue_continue.ps1
# Winner decision file: experiments/campaign/winner_decision.txt
#   one line: <model key>   e.g. resegs_a2   or   resegs_a3 --vrex-lambda 0.3

$ErrorActionPreference = 'Continue'
$log = 'experiments/campaign/queue.log'

function Write-Log([string]$msg) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Output $line
}

# Wait for the main queue driver to exit (marker: QUEUE_END in queue.log).
while ($true) {
    $tail = Get-Content $log -Tail 1 -ErrorAction SilentlyContinue
    if ($tail -match 'QUEUE_END') { break }
    Start-Sleep -Seconds 120
}
Write-Log 'CONT_QUEUE_START'

$decisionPath = 'experiments/campaign/winner_decision.txt'
if (-not (Test-Path $decisionPath)) {
    Write-Log 'CONT_ABORT no winner_decision.txt'
    exit 1
}
$decision = (Get-Content $decisionPath -TotalCount 1).Trim()
Write-Log ("CONT_WINNER " + $decision)

$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$env:KMP_DUPLICATE_LIB_OK = 'TRUE'
$env:PYTHONUTF8 = '1'

$data = 'data/processed/protocols/temporal_balanced_no_temporal.pt'
$py = 'uv run python'
$extra = ''
if ($decision -eq 'resegs_a3_lam0.1') { $decision = 'resegs_a3'; $extra = '--vrex-lambda 0.1' }
if ($decision -eq 'resegs_a3_lam0.3') { $decision = 'resegs_a3'; $extra = '--vrex-lambda 0.3' }
if ($decision -eq 'resegs_a3_lam1.0') { $decision = 'resegs_a3'; $extra = '--vrex-lambda 1.0' }

$steps = @(
    @{ name = 'winner_s42_200ep';   args = "$py scripts/run_sprint1.py --data $data --models $decision --seed 42 --run-name dg_winner_s42 $extra" },
    @{ name = 'winner_s3407_200ep'; args = "$py scripts/run_sprint1.py --data $data --models $decision --seed 3407 --run-name dg_winner_s3407 $extra" },
    @{ name = 'winner_s1234_200ep'; args = "$py scripts/run_sprint1.py --data $data --models $decision --seed 1234 --run-name dg_winner_s1234 $extra" }
)
foreach ($s in $steps) {
    $os = Get-CimInstance Win32_OperatingSystem
    Write-Log ('STEP_START {0} freeRAM_GB={1}' -f $s.name, [math]::Round($os.FreePhysicalMemory / 1MB, 2))
    $p = Start-Process -FilePath 'cmd' -ArgumentList '/c', $s.args -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput ('experiments/campaign/queue_stdout_{0}.log' -f $s.name) `
        -RedirectStandardError ('experiments/campaign/queue_stderr_{0}.log' -f $s.name)
    try { $p.PriorityClass = 'BelowNormal' } catch { }
    $p.WaitForExit()
    $code = $p.ExitCode
    $metricsOk = Test-Path ('experiments/campaign/runs/{0}/metrics.csv' -f $s.name)
    if (($null -ne $code -and $code -eq 0) -or $metricsOk) { Write-Log ('STEP_DONE {0} exit={1} artifact_ok={2}' -f $s.name, $code, $metricsOk) }
    else { Write-Log ('STEP_FAIL {0} exit={1}' -f $s.name, $code) }
    Start-Sleep -Seconds 10
}

# Single pre-registered test opening (per seed, once) for frozen configurations.
$testTargets = @('e0_egs_s42\egs', 'e0_egs_s3407\egs', 'e0_egs_s1234\egs',
    'dg_winner_s42\' + $decision, 'dg_winner_s3407\' + $decision, 'dg_winner_s1234\' + $decision,
    'e1_dir_sage_s42\dir_sage', 'e1_dir_sage_s3407\dir_sage', 'e1_dir_sage_s1234\dir_sage')
foreach ($t in $testTargets) {
    $runDir = 'experiments/campaign/runs/' + $t
    if (-not (Test-Path ('{0}/model_config.json' -f $runDir))) { Write-Log ('TEST_SKIP {0} missing' -f $t); continue }
    Write-Log ('TEST_OPEN {0}' -f $t)
    cmd /c "$py scripts/evaluate_final_test.py --run-dir $runDir --confirm-frozen" 2>&1 |
        Out-File -FilePath ('experiments/campaign/finaltest_{0}.log' -f ($t -replace '\\', '_')) -Encoding UTF8
    Write-Log ('TEST_DONE {0}' -f $t)
    Start-Sleep -Seconds 5
}
Write-Log 'CONT_QUEUE_END'
