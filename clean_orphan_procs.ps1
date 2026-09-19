param(
    [switch]$DryRun
)

# Clean ONLY orphaned duplicate engine/API processes launched with SYSTEM python
# (path contains Python311, NOT the project venv). Official venv processes are
# left for STOP.ps1.

$targets = Get-CimInstance Win32_Process | Where-Object {
    $cmd = $_.CommandLine
    ($_.Name -like "python*.exe") -and
    ($cmd -match 'Python311') -and
    (($cmd -match 'main\.py') -or ($cmd -match 'uvicorn api\.app:app'))
}

foreach ($p in $targets) {
    Write-Host "PID=$($p.ProcessId) CMD=$($p.CommandLine)"
    if (-not $DryRun) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  -> stopped"
    }
}