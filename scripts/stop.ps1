$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Require-Administrator

Write-SystemLog "Stopping NetworkMonitor."
Write-SupervisorLog "STOP invoked."

$OverallSuccess = $true

# =====================================
# Stop in reverse order of startup
# =====================================

# Helper: stop one service by key, then verify its ports are closed.
function Stop-ServiceByKey {
    param(
        [string]$Key
    )

    $svc = Get-ServiceDefinition -Key $Key
    if (-not $svc) {
        Write-ErrorLog "Stop: unknown service key '$Key'."
        return $false
    }

    $Name = $svc.Name
    $PidFile = $svc.PidFile
    $Ports = $svc.Ports
    $ProcessNames = $svc.Process

    Write-SystemLog "=== Stopping $Name ==="

    $pidValue = $null
    try {
        $pidValue = Get-ProcessIdFromFile -PidFilePath $PidFile
    } catch {
        Write-SystemLog "${Name}: PID file corrupt, removing." "WARN"
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        $pidValue = $null
    }

    $killed = $true

    if ($pidValue -and (Test-ProcessAlive $pidValue)) {
        # Verify the PID belongs to the expected process image (defend against PID reuse).
        if (Test-PidOwner -ProcessId $pidValue -ExpectedNames $ProcessNames) {
            $killed = Stop-ProcessTree -Name $Name -RootProcessId $pidValue -GracefulTimeout 10 -ForceTimeout 3
            if (-not $killed) {
                Write-ErrorLog "${Name}: tree kill did not complete."
                $OverallSuccess = $false
            }
        } else {
            Write-SystemLog "${Name}: PID $pidValue is NOT a '$($ProcessNames -join '/')' process (PID reuse). Not killing. Removing PID file." "WARN"
        }
    } else {
        Write-SystemLog "${Name}: no live process for PID file, skipping kill."
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

    # Even if PID file was absent/stale, an orphan process may still own the port.
    # Verify the ports are now closed; if not, find the listener by port and kill it.
    foreach ($port in $Ports) {
        $attempt = 0
        while ((Test-Port "127.0.0.1" $port 1000) -and $attempt -lt 10) {
            if ($attempt -eq 0) {
                Write-SystemLog "${Name}: port $port still open after PID-based stop; locating listener." "WARN"
            }

            # Find the PID listening on the port.
            $listener = $null
            try {
                $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
                if ($conns) {
                    $listener = $conns | Select-Object -First 1 -ExpandProperty OwningProcess
                }
            } catch { }

            if ($listener -and $listener -gt 0) {
                Write-SystemLog "${Name}: force-killing orphan listener PID $listener on port $port."
                Stop-ProcessTree -Name "$Name (orphan)" -RootProcessId ([int]$listener) -GracefulTimeout 2 -ForceTimeout 2 | Out-Null
            }

            Start-Sleep -Seconds 1
            $attempt++
        }

        if (Test-Port "127.0.0.1" $port 1000) {
            Write-ErrorLog "${Name}: port $port is STILL open after stop."
            $OverallSuccess = $false
        } else {
            Write-SystemLog "${Name}: port $port closed."
        }
    }

    return $killed
}

# 1. Dashboard (stop first - user-facing)
Stop-ServiceByKey -Key "dashboard" | Out-Null

# 2. API
Stop-ServiceByKey -Key "api" | Out-Null

# 3. Network Engine
Stop-ServiceByKey -Key "engine" | Out-Null

# Note: PostgreSQL is a system service and is intentionally not stopped here.

Write-SystemLog "============================================"
if ($OverallSuccess) {
    Write-SystemLog "NetworkMonitor stopped successfully."
    Write-SupervisorLog "STOP completed: OK."
    Write-Host "STOP RESULT=OK"
    exit 0
} else {
    Write-SystemLog "NetworkMonitor stopped with errors." "ERROR"
    Write-SupervisorLog "STOP completed: ERROR."
    Write-Host "STOP RESULT=ERROR"
    exit 1
}