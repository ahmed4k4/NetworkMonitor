$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Require-Administrator

Write-SystemLog "Starting NetworkMonitor."


# =====================================
# PostgreSQL
# =====================================

$Postgres = Get-Service |
    Where-Object {
        $_.Name -like "postgresql*"
    } |
    Select-Object -First 1


if ($Postgres) {

    if ($Postgres.Status -ne "Running") {

        Write-SystemLog `
            "Starting PostgreSQL."

        Start-Service $Postgres.Name

        Start-Sleep -Seconds 3
    }

    Write-SystemLog `
        "PostgreSQL status: $($Postgres.Status)"

} else {

    Write-SystemLog `
        "PostgreSQL service not found." `
        "ERROR"

    exit 1
}


# =====================================
# Network Engine
# =====================================

$EnginePython = Join-Path `
    $Root `
    "network-engine\.venv\Scripts\python.exe"


if (!(Test-Path $EnginePython)) {

    Write-SystemLog `
        "Engine Python executable not found." `
        "ERROR"

    exit 1
}


Write-SystemLog `
    "Starting Network Engine."


$EngineProcess = Start-Process `
    -FilePath $EnginePython `
    -ArgumentList "main.py" `
    -WorkingDirectory "$Root\network-engine" `
    -RedirectStandardOutput `
        "$Root\logs\engine.out.log" `
    -RedirectStandardError `
        "$Root\logs\engine.error.log" `
    -PassThru


$EngineProcess.Id |
    Set-Content "$Root\data\runtime\engine.pid"


Write-SystemLog `
    "Network Engine PID: $($EngineProcess.Id)"


# =====================================
# API
# =====================================

Write-SystemLog `
    "Starting API."

$ApiProcess = Start-Process `
    -FilePath $EnginePython `
    -ArgumentList "-m uvicorn api.app:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory "$Root\network-engine" `
    -RedirectStandardOutput `
        "$Root\logs\api.out.log" `
    -RedirectStandardError `
        "$Root\logs\api.error.log" `
    -PassThru


$ApiProcess.Id |
    Set-Content "$Root\data\runtime\api.pid"


Write-SystemLog `
    "API PID: $($ApiProcess.Id)"


# =====================================
# Wait for API
# =====================================

Write-SystemLog `
    "Waiting for API."

$ApiReady = $false

for ($i = 0; $i -lt 20; $i++) {

    if (Test-Port "127.0.0.1" 8000) {

        $ApiReady = $true

        break
    }

    Start-Sleep -Seconds 1
}


if (!$ApiReady) {

    Write-SystemLog `
        "API failed to start." `
        "ERROR"

    exit 1
}


Write-SystemLog `
    "API is ready."


# =====================================
# Dashboard
# =====================================

Write-SystemLog `
    "Starting dashboard."


$DashboardProcess = Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList "run start" `
    -WorkingDirectory "$Root\dashboard" `
    -RedirectStandardOutput `
        "$Root\logs\dashboard.out.log" `
    -RedirectStandardError `
        "$Root\logs\dashboard.error.log" `
    -PassThru


$DashboardProcess.Id |
    Set-Content "$Root\data\runtime\dashboard.pid"


Write-SystemLog `
    "Dashboard PID: $($DashboardProcess.Id)"


# =====================================
# Final
# =====================================

Start-Sleep -Seconds 3

Write-SystemLog `
    "NetworkMonitor started successfully."

Start-Process `
    "http://localhost:3000"