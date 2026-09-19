$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

. "$PSScriptRoot\engine-health.ps1"

Require-Administrator

Write-SystemLog "Starting NetworkMonitor."
Write-SupervisorLog "START invoked."

$OverallSuccess = $true

# =====================================
# 1. PostgreSQL (must be first - all other services depend on it)
# =====================================

Write-SystemLog "=== Starting PostgreSQL ==="

$Postgres = Get-Service |
    Where-Object {
        $_.Name -like "postgresql*"
    } |
    Select-Object -First 1

if (-not $Postgres) {
    Write-ErrorLog "PostgreSQL service not found."
    Write-Host "POSTGRES RESULT=FAILED"
    exit 1
}

if ($Postgres.Status -ne "Running") {
    Write-SystemLog "Starting PostgreSQL service..."
    try {
        Start-Service $Postgres.Name -ErrorAction Stop
    } catch {
        Write-ErrorLog "Failed to start PostgreSQL: $($_.Exception.Message)"
        Write-Host "POSTGRES RESULT=FAILED"
        exit 1
    }
}

# Wait for PostgreSQL to be ready
$pgReady = $false
for ($i = 0; $i -lt 30; $i++) {
    if (Test-PostgreSQL) {
        $pgReady = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $pgReady) {
    Write-ErrorLog "PostgreSQL did not become ready in time."
    Write-Host "POSTGRES RESULT=FAILED"
    exit 1
}

Write-SystemLog "PostgreSQL is healthy."
Write-Host "POSTGRES RESULT=READY"


# =====================================
# 2. Network Engine
# =====================================

Write-SystemLog "=== Starting Network Engine ==="

$EnginePython = Join-Path `
    $Root `
    "network-engine\.venv\Scripts\python.exe"

if (-not (Test-Path $EnginePython)) {
    Write-ErrorLog "Engine Python executable not found at $EnginePython."
    Write-Host "ENGINE RESULT=FAILED"
    exit 1
}

$enginePidFilePath = Join-Path $Root "data\runtime\engine.pid"
$engineOutLog = Join-Path $Root "logs\engine.out.log"
$engineErrLog = Join-Path $Root "logs\engine.error.log"

# Check if already running
$existingEngineId = Get-ProcessIdFromFile -PidFilePath $enginePidFilePath
if ($existingEngineId -and (Test-ProcessAlive $existingEngineId)) {
    Write-SystemLog "Network Engine already running with PID $existingEngineId."
    # Re-verify liveness even if the pid file says "running"
    if (Test-EngineLogReady -LogFile $engineErrLog -ProcessId $existingEngineId) {
        Write-SystemLog "Network Engine is confirmed healthy (log sentinel + process alive)."
        Write-Host "ENGINE RESULT=STARTED"
    } else {
        Write-SystemLog "Network Engine process exists but is NOT healthy (no log sentinel)." "WARN"
        Write-Host "ENGINE RESULT=FAILED"
        $OverallSuccess = $false
    }
} else {
    Write-SystemLog "No running engine process found; starting a new one."

    $success = Start-ServiceProcess `
        -Name "Network Engine" `
        -Executable $EnginePython `
        -Arguments "main.py" `
        -WorkingDirectory "$Root\network-engine" `
        -StdOutLog $engineOutLog `
        -StdErrLog $engineErrLog `
        -PidFile $enginePidFilePath `
        -HealthCheck {
            param($pidValue)
            Test-EngineLogReady -LogFile $engineErrLog -ProcessId $pidValue
        } `
        -HealthCheckTimeout 120

    if ($success) {
        Write-SystemLog "Network Engine confirmed ready (log sentinel present)."
    } else {
        Write-SystemLog "Network Engine failed to start or verify." "ERROR"
        Write-Host "ENGINE RESULT=FAILED"
        $OverallSuccess = $false
    }
}


# =====================================
# 3. API (separate process for better isolation)
# =====================================

Write-SystemLog "=== Starting API ==="

$apiPidFilePath = Join-Path $Root "data\runtime\api.pid"
$apiOutLog = Join-Path $Root "logs\api.out.log"
$apiErrLog = Join-Path $Root "logs\api.error.log"

$existingApiId = Get-ProcessIdFromFile -PidFilePath $apiPidFilePath
if ($existingApiId -and (Test-ProcessAlive $existingApiId)) {
    Write-SystemLog "API already running with PID $existingApiId."
    if (Test-HTTP "http://127.0.0.1:8000/api/health") {
        Write-SystemLog "API health endpoint responding."
        Write-Host "API RESULT=STARTED"
    } else {
        Write-SystemLog "API process exists but /api/health not OK." "WARN"
        Write-Host "API RESULT=FAILED"
        $OverallSuccess = $false
    }
} else {
    Write-SystemLog "No running API process found; starting a new one."

    $success = Start-ServiceProcess `
        -Name "API" `
        -Executable $EnginePython `
        -Arguments "-m uvicorn api.app:app --host 127.0.0.1 --port 8000" `
        -WorkingDirectory "$Root\network-engine" `
        -StdOutLog $apiOutLog `
        -StdErrLog $apiErrLog `
        -PidFile $apiPidFilePath `
        -HealthCheck { Test-HTTP "http://127.0.0.1:8000/api/health" } `
        -HealthCheckTimeout 120

    if ($success) {
        Write-SystemLog "API confirmed healthy via /api/health."
    } else {
        Write-SystemLog "API failed to start or verify." "ERROR"
        Write-Host "API RESULT=FAILED"
        $OverallSuccess = $false
    }
}


# =====================================
# 4. Dashboard
# =====================================

Write-SystemLog "=== Starting Dashboard ==="

$dashboardPidFilePath = Join-Path $Root "data\runtime\dashboard.pid"
$dashboardOutLog = Join-Path $Root "logs\dashboard.out.log"
$dashboardErrLog = Join-Path $Root "logs\dashboard.error.log"

$existingDashId = Get-ProcessIdFromFile -PidFilePath $dashboardPidFilePath
if ($existingDashId -and (Test-ProcessAlive $existingDashId)) {
    Write-SystemLog "Dashboard already running with PID $existingDashId."
    if (Test-DashReady -Hostname "127.0.0.1" -Port 3000) {
        Write-SystemLog "Dashboard HTTP 200 confirmed."
        Write-Host "DASHBOARD RESULT=STARTED"
    } else {
        Write-SystemLog "Dashboard process exists but HTTP not serving." "WARN"
        Write-Host "DASHBOARD RESULT=FAILED"
        $OverallSuccess = $false
    }
} else {
    Write-SystemLog "No running dashboard process found; starting a new one."

    # Resolve the npm launcher to an absolute path. Start-Process does NOT
    # resolve bare "npm.cmd" via PATH on all systems (npm is a .cmd shim),
    # which previously caused "executable not found: 'npm.cmd'".
    $npmCmd = $null
    $npmResolved = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmResolved) {
        $npmCmd = $npmResolved.Source
    } else {
        $npmResolved = Get-Command npm -ErrorAction SilentlyContinue
        if ($npmResolved) { $npmCmd = $npmResolved.Source }
    }

    if (-not $npmCmd -or -not (Test-Path $npmCmd)) {
        Write-SystemLog "npm launcher not found on PATH." "ERROR"
        Write-Host "DASHBOARD RESULT=FAILED"
        $OverallSuccess = $false
    } else {
        $success = Start-ServiceProcess `
            -Name "Dashboard" `
            -Executable $npmCmd `
            -Arguments "run start" `
            -WorkingDirectory "$Root\dashboard" `
            -StdOutLog $dashboardOutLog `
            -StdErrLog $dashboardErrLog `
            -PidFile $dashboardPidFilePath `
            -HealthCheck { Test-DashReady -Hostname "127.0.0.1" -Port 3000 } `
            -HealthCheckTimeout 180

        if ($success) {
            Write-SystemLog "Dashboard confirmed ready (HTTP 200 on :3000)."
        } else {
            Write-SystemLog "Dashboard failed to start or verify." "ERROR"
            Write-Host "DASHBOARD RESULT=FAILED"
            $OverallSuccess = $false
        }
    }
}


# =====================================
# Final Status
# =====================================

if ($OverallSuccess) {
    Write-SystemLog "============================================"
    Write-SystemLog "NetworkMonitor started successfully."
    Write-SystemLog "============================================"
    Write-Host ""
    Write-Host "Service Status:"
    & "$PSScriptRoot\status.ps1"
    Write-Host ""
    Write-Host "Dashboard: http://localhost:3000"
    Write-Host "API:       http://localhost:8000"
    Write-Host "API Docs:  http://localhost:8000/docs"
    
    # Optionally open browser
    if ($env:OPEN_BROWSER -ne "false") {
        Start-Process "http://localhost:3000"
    }
    Write-Host "START RESULT=OK"
    exit 0
} else {
    Write-SystemLog "NetworkMonitor started with errors. Check logs." "ERROR"
    Write-SupervisorLog "START finished with errors."
    Write-Host "START RESULT=ERROR"
    exit 1
}