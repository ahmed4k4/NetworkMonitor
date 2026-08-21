$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Require-Administrator

Write-SystemLog "Stopping NetworkMonitor."


function Stop-ManagedProcess {

    param(
        [string]$Name,
        [string]$PidFile
    )

    if (!(Test-Path $PidFile)) {
        return
    }

    $ProcessId = Get-Content $PidFile

    if ($ProcessId) {

        $Process = Get-Process `
            -Id $ProcessId `
            -ErrorAction SilentlyContinue

        if ($Process) {

            Write-SystemLog `
                "Stopping $Name PID $ProcessId."

            Stop-Process `
                -Id $ProcessId `
                -Force
        }
    }

    Remove-Item `
        $PidFile `
        -Force `
        -ErrorAction SilentlyContinue
}


# Dashboard
Stop-ManagedProcess `
    "Dashboard" `
    "$Root\data\runtime\dashboard.pid"


# API
Stop-ManagedProcess `
    "API" `
    "$Root\data\runtime\api.pid"


# Engine
Stop-ManagedProcess `
    "Engine" `
    "$Root\data\runtime\engine.pid"


Write-SystemLog `
    "NetworkMonitor stopped."