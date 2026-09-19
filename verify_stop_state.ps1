$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== POST-STOP STATE VERIFICATION ==="

Write-Host "--- PID files in logs ---"
$pids = Get-ChildItem "e:\NetworkMonitor\logs" -Filter "*.pid"
if ($pids) {
    $pids | ForEach-Object { Write-Host ("  FOUND: " + $_.Name) }
} else {
    Write-Host "  none found (cleaned)"
}

Write-Host "--- Ports ---"
$engine = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -WarningAction SilentlyContinue
$dash = Test-NetConnection -ComputerName 127.0.0.1 -Port 3000 -WarningAction SilentlyContinue
Write-Host ("  port 8000 open: " + $engine.TcpTestSucceeded)
Write-Host ("  port 3000 open: " + $dash.TcpTestSucceeded)

Write-Host "--- PostgreSQL (intended to stay up) ---"
$svc = Get-Service -Name "*postgres*"
$svc | Select-Object Name, Status | Format-Table -AutoSize

Write-Host "--- App processes check ---"
Write-Host ("  engine py alive: " + [bool](Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*\.venv\*" }))
Write-Host ("  node next alive: " + [bool](Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*next*" -or $_.MainWindowTitle -like "*next*" }))
</write_to_file>