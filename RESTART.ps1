$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Restarting NetworkMonitor..."

# 1. Stop (canonical stop with tree kill + port verification)
$stopResult = & "$Root\scripts\stop.ps1"
$stopExitCode = $LASTEXITCODE

if ($stopExitCode -ne 0) {
    Write-Host "Stop failed with exit code $stopExitCode" -ForegroundColor Red
    exit $stopExitCode
}

# Wait for clean shutdown and port release
Write-Host "Waiting for services to fully stop..."
Start-Sleep -Seconds 3

# 2. Start (PostgreSQL -> Engine -> API -> Dashboard)
$startResult = & "$Root\scripts\start.ps1"
$startExitCode = $LASTEXITCODE

if ($startExitCode -ne 0) {
    Write-Host "Start failed with exit code $startExitCode" -ForegroundColor Red
    exit $startExitCode
}

# 3. Health verification
Write-Host ""
Write-Host "Running post-restart health verification..."
$healthResult = & "$Root\scripts\health.ps1"
$healthExitCode = $LASTEXITCODE

if ($healthExitCode -ne 0) {
    Write-Host "Restart completed but health check reported issues." -ForegroundColor Yellow
    exit $healthExitCode
}

Write-Host "NetworkMonitor restarted successfully." -ForegroundColor Green
exit 0