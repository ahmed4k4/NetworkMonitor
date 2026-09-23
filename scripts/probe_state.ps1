$Root = Split-Path -Parent $PSScriptRoot
Write-Host "=== LISTENING PORTS 8000/3000 ==="
Get-NetTCPConnection -LocalPort 8000,3000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalPort, OwningProcess
Write-Host ""
Write-Host "=== PID FILES ==="
$pidDir = Join-Path $Root "data\runtime"
if (Test-Path $pidDir) {
    Get-ChildItem (Join-Path $pidDir "*.pid") -ErrorAction SilentlyContinue | ForEach-Object {
        $c = (Get-Content $_.FullName -Raw).Trim()
        Write-Host ("  {0}: PID={1}" -f $_.Name, $c)
        $proc = Get-Process -Id ([int]$c) -ErrorAction SilentlyContinue
        if ($proc) { Write-Host ("      -> alive: {0}" -f $proc.ProcessName) }
        else { Write-Host "      -> NOT ALIVE (stale)" }
    }
} else {
    Write-Host "  runtime dir missing"
}