# Sprint-1 serial queue driver: strictly ONE training process at a time.
# A failed step is logged and the queue continues; every exit code is recorded.
# Usage: powershell -NoProfile -File scripts/campaign_queue.ps1
# Log:   experiments/campaign/queue.log (START/DONE/FAIL lines; use with watchdog.log)

$ErrorActionPreference = 'Continue'
$log = 'experiments/campaign/queue.log'

function Write-Log([string]$msg) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Output $line
}

$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$env:KMP_DUPLICATE_LIB_OK = 'TRUE'
$env:PYTHONUTF8 = '1'

$data = 'data/processed/protocols/temporal_balanced_no_temporal.pt'
$py = 'uv run python'

# Resource rule (user directive 2026-09-06): NO parallel experiments.
# Order: screens first (80ep, quick val signal for DG-ResEGS), then the formal
# E0 anchor (200ep), GBDT, and Dir-SAGE baselines. All val-first; test stays
# closed until the pre-registered --final-test stage.
$steps = @(
    @{ name = 'screen_a0_egs_s42';    args = "$py scripts/run_sprint1.py --data $data --models egs --seed 42 --epochs 80 --early-stopping-patience 20 --run-name screen_a0_egs_s42" },
    @{ name = 'screen_a1_s42';        args = "$py scripts/run_sprint1.py --data $data --models resegs_a1 --seed 42 --epochs 80 --early-stopping-patience 20 --run-name screen_a1_s42" },
    @{ name = 'screen_a2_s42';        args = "$py scripts/run_sprint1.py --data $data --models resegs_a2 --seed 42 --epochs 80 --early-stopping-patience 20 --run-name screen_a2_s42" },
    @{ name = 'screen_a3_lam0.1_s42'; args = "$py scripts/run_sprint1.py --data $data --models resegs_a3 --vrex-lambda 0.1 --seed 42 --epochs 80 --early-stopping-patience 20 --run-name screen_a3_lam0.1_s42" },
    @{ name = 'screen_a3_lam0.3_s42'; args = "$py scripts/run_sprint1.py --data $data --models resegs_a3 --vrex-lambda 0.3 --seed 42 --epochs 80 --early-stopping-patience 20 --run-name screen_a3_lam0.3_s42" },
    @{ name = 'screen_a3_lam1.0_s42'; args = "$py scripts/run_sprint1.py --data $data --models resegs_a3 --vrex-lambda 1.0 --seed 42 --epochs 80 --early-stopping-patience 20 --run-name screen_a3_lam1.0_s42" },
    @{ name = 'e0_egs_s42';           args = "$py scripts/run_sprint1.py --data $data --models egs --seed 42 --run-name e0_egs_s42" },
    @{ name = 'e2_gbdt_3seeds';       args = "$py scripts/run_tabular_baseline.py --data $data --run-name e2_gbdt_3seeds" },
    @{ name = 'e0_egs_s3407';         args = "$py scripts/run_sprint1.py --data $data --models egs --seed 3407 --run-name e0_egs_s3407" },
    @{ name = 'e0_egs_s1234';         args = "$py scripts/run_sprint1.py --data $data --models egs --seed 1234 --run-name e0_egs_s1234" },
    @{ name = 'e1_dir_sage_s42';      args = "$py scripts/run_sprint1.py --data $data --models dir_sage --seed 42 --run-name e1_dir_sage_s42" },
    @{ name = 'e1_dir_sage_s3407';    args = "$py scripts/run_sprint1.py --data $data --models dir_sage --seed 3407 --run-name e1_dir_sage_s3407" },
    @{ name = 'e1_dir_sage_s1234';    args = "$py scripts/run_sprint1.py --data $data --models dir_sage --seed 1234 --run-name e1_dir_sage_s1234" }
)

Write-Log ('QUEUE_START total_steps=' + $steps.Count + ' rule=strictly_serial_one_trainer')
foreach ($s in $steps) {
    $os = Get-CimInstance Win32_OperatingSystem
    Write-Log ('STEP_START {0} freeRAM_GB={1}' -f $s.name, [math]::Round($os.FreePhysicalMemory / 1MB, 2))
    $p = Start-Process -FilePath 'cmd' -ArgumentList '/c', $s.args -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput ('experiments/campaign/queue_stdout_{0}.log' -f $s.name) `
        -RedirectStandardError ('experiments/campaign/queue_stderr_{0}.log' -f $s.name)
    try { $p.PriorityClass = 'BelowNormal' } catch { Write-Log ('PRIORITY_WARN {0} {1}' -f $s.name, $_.Exception.Message) }
    $p.WaitForExit()
    $code = $p.ExitCode
    # ExitCode can be null even on success (PS quirk); confirm with artifacts.
    $metricsOk = (Test-Path ('experiments/campaign/runs/{0}/metrics.csv' -f $s.name)) -or (Test-Path ('experiments/campaign/runs/{0}/metrics.json' -f $s.name))
    if ($null -ne $code -and $code -eq 0) {
        Write-Log ('STEP_DONE {0} exit=0' -f $s.name)
    } elseif ($metricsOk) {
        Write-Log ('STEP_DONE {0} exit={1} artifact_ok=true (null exit code treated as success)' -f $s.name, $code)
    } else {
        Write-Log ('STEP_FAIL {0} exit={1} artifact_ok=false' -f $s.name, $code)
    }
    Start-Sleep -Seconds 10
}
Write-Log 'QUEUE_END'
