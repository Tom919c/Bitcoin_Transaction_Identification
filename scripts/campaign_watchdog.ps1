# 冲刺一实验链看门狗：监控后台训练进程、内存、进度停滞与 CPU 活动。
# 用法：powershell -NoProfile -File scripts/campaign_watchdog.ps1 [-IntervalSec 120] [-StallMin 20]
# 日志：experiments/campaign/watchdog.log（本地证据；含 ALERT 行时需人工介入）

param(
    [int]$IntervalSec = 120,
    [int]$StallMin = 20
)

$ErrorActionPreference = 'Continue'
$log = 'experiments/campaign/watchdog.log'
$chainLogs = @(
    'experiments/campaign/queue.log'
)

function Write-Log([string]$msg) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
}

Write-Log "watchdog started interval=${IntervalSec}s stall_threshold=${StallMin}min"
$lastProgress = Get-Date
$lastCpuSum = -1.0

while ($true) {
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)

        $pyprocs = @(Get-Process python -ErrorAction SilentlyContinue)
        $nproc = $pyprocs.Count
        $cpuSum = [math]::Round((($pyprocs | Measure-Object -Property CPU -Sum).Sum), 1)
        $cpuDelta = if ($lastCpuSum -ge 0) { [math]::Round($cpuSum - $lastCpuSum, 1) } else { -1 }
        $lastCpuSum = $cpuSum

        $ckpt = Get-ChildItem 'experiments/campaign/runs' -Recurse -Filter 'best.pt' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $logNewest = Get-ChildItem $chainLogs -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $newestTime = ($ckpt, $logNewest) |
            Where-Object { $_ } | Measure-Object -Property LastWriteTime -Maximum | Select-Object -ExpandProperty Maximum
        if ($newestTime -and ((Get-Date) - $newestTime).TotalMinutes -le 5) { $lastProgress = Get-Date }
        $stall = [math]::Round(((Get-Date) - $lastProgress).TotalMinutes, 1)

        $ckptInfo = if ($ckpt) { '{0}@{1}' -f $ckpt.Directory.Parent.Name, (Get-Date $ckpt.LastWriteTime -Format 'HH:mm:ss') } else { 'none' }
        $queueLast = try { (Get-Content 'experiments/campaign/queue.log' -Tail 1 -ErrorAction Stop) } catch { 'queue.log missing' }
        $msg = 'procs={0} cpuSum={1}s cpuDelta={2}s/interval freeRAM={3}GB newest_ckpt={4} stall={5}min queue=[{6}]' -f $nproc, $cpuSum, $cpuDelta, $freeGB, $ckptInfo, $stall, $queueLast

        if ($nproc -eq 0) {
            $msg = 'ALERT NO_PYTHON_PROC chains_may_have_finished_or_died ' + $msg
        }
        if ($freeGB -lt 1.5) {
            $msg = 'ALERT LOW_MEM ' + $msg
        }
        if ($nproc -gt 0 -and $stall -gt $StallMin) {
            $msg = 'ALERT STALLED_NO_PROGRESS ' + $msg
        }
        Write-Log $msg
    }
    catch {
        Write-Log ('ALERT WATCHDOG_ERROR ' + $_.Exception.Message)
    }
    Start-Sleep -Seconds $IntervalSec
}
