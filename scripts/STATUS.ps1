$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"
. "$PSScriptRoot\engine-health.ps1"

Write-SystemLog "=== STATUS ==="

Write-Host ""
Write-Host "========================================"
Write-Host "       NETWORK MONITOR STATUS"
Write-Host "========================================"
Write-Host ""

$AnyIssues = $false

function Show-ServiceStatus {
    param(
        [string]$Name,
        [string]$PidFile,
        [string[]]$ProcessNames = @(),
        [scriptblock]$HealthCheck = $null
    )

    # For services without PID files (like PostgreSQL service)
    if (-not $PidFile -or $PidFile -eq "") {
        if ($HealthCheck) {
            $healthy = $false
            try {
                $healthy = & $HealthCheck
            } catch {
                Write-ErrorLog "$Name health check raised: $($_.Exception.Message)"
            }
            if ($healthy) {
                Write-Host "  $Name : RUNNING  [HEALTHY]" -ForegroundColor Green
            } else {
                Write-Host "  $Name : STOPPED/UNHEALTHY" -ForegroundColor Red
                $script:AnyIssues = $true
            }
        } else {
            Write-Host "  $Name : UNKNOWN (no health check)" -ForegroundColor Yellow
            $script:AnyIssues = $true
        }
        return
    }

    if (!(Test-Path $PidFile)) {
        Write-Host "  $Name : STOPPED" -ForegroundColor Red
        $script:AnyIssues = $true
        return
    }

    $ProcessId = $null
    try {
        $ProcessId = Get-ProcessIdFromFile -PidFilePath $PidFile
    } catch {
        Write-ErrorLog "$Name PID file is corrupt: $($_.Exception.Message)"
        Write-Host "  $Name : INVALID PID FILE" -ForegroundColor Red
        $script:AnyIssues = $true
        return
    }

    if (-not $ProcessId) {
        Write-Host "  $Name : INVALID PID FILE" -ForegroundColor Red
        $script:AnyIssues = $true
        return
    }

    $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue

    if (-not $Process) {
        Write-Host "  $Name : CRASHED (PID $ProcessId not found)" -ForegroundColor Red
        $script:AnyIssues = $true
        Write-SupervisorLog "$Name CRASHED (PID $ProcessId not found)."
        return
    }

    # PID ownership check: reject a recycled PID that now belongs to another program.
    if ($ProcessNames -and $ProcessNames.Count -gt 0) {
        if (-not (Test-PidOwner -ProcessId $ProcessId -ExpectedNames $ProcessNames)) {
            Write-Host "  $Name : WRONG PROCESS (PID $ProcessId is '$($Process.ProcessName)', not '$($ProcessNames -join '/')')" -ForegroundColor Red
            $script:AnyIssues = $true
            Write-SupervisorLog "$Name PID $ProcessId belongs to '$($Process.ProcessName)', not the expected process."
            return
        }
    }

    $baseStatus = "  $Name : RUNNING  PID=$ProcessId"

    if ($HealthCheck) {
        $healthy = $false
        try {
            $healthy = & $HealthCheck $ProcessId
        } catch {
            $healthy = $false
            Write-ErrorLog "$Name health check raised: $($_.Exception.Message)"
        }
        if ($healthy) {
            Write-Host "$baseStatus  [HEALTHY]" -ForegroundColor Green
        } else {
            Write-Host "$baseStatus  [UNHEALTHY]" -ForegroundColor Yellow
            $script:AnyIssues = $true
            Write-SupervisorLog "$Name UNHEALTHY (PID $ProcessId)."
        }
    } else {
        Write-Host "$baseStatus" -ForegroundColor Green
    }
}


Write-Host "CORE SERVICES:"
Write-Host ""

Show-ServiceStatus `
    "PostgreSQL" `
    "" `
    @() `
    { Test-PostgreSQL }

$engineDef = Get-ServiceDefinition -Key "engine"
$engineErrLog = $engineDef.ErrLog

Show-ServiceStatus `
    "Network Engine" `
    $engineDef.PidFile `
    $engineDef.Process `
    {
        param($processId)
        Test-EngineLogReady -LogFile $engineErrLog -ProcessId $processId
    }

$apiDef = Get-ServiceDefinition -Key "api"

Show-ServiceStatus `
    "API" `
    $apiDef.PidFile `
    $apiDef.Process `
    { Test-HTTP "http://127.0.0.1:8000/api/health" }

$dashboardDef = Get-ServiceDefinition -Key "dashboard"

Show-ServiceStatus `
    "Dashboard" `
    $dashboardDef.PidFile `
    $dashboardDef.Process `
    { Test-DashReady -Hostname "127.0.0.1" -Port 3000 }


Write-Host ""

# WebSocket check (API process hosts the WS endpoint on :8000)
Write-Host "WebSocket: "
if (Test-HTTP "http://127.0.0.1:8000/api/health") {
    Write-Host "  WebSocket endpoint available on port 8000 (via API)" -ForegroundColor Green
} else {
    Write-Host "  WebSocket endpoint not reachable" -ForegroundColor Red
    $AnyIssues = $true
}


Write-Host ""

# Network Interface
Write-Host "NETWORK:"
Write-Host ""

$lanAdapter = Get-NetAdapter -Name $script:LanInterface -ErrorAction SilentlyContinue
if ($lanAdapter) {
    Write-Host "  $script:LanInterface : $($lanAdapter.Status)"
    if ($lanAdapter.Status -ne "Up") { $AnyIssues = $true }
} else {
    Write-Host "  $script:LanInterface : NOT FOUND" -ForegroundColor Red
    $AnyIssues = $true
}

$lanIp = Get-NetIPAddress -InterfaceAlias $script:LanInterface -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($lanIp) {
    Write-Host "  IPv4     : $($lanIp.IPAddress)"
} else {
    Write-Host "  IPv4     : NOT CONFIGURED" -ForegroundColor Yellow
}


Write-Host ""

# Overall
Write-Host "========================================"
if ($AnyIssues) {
    Write-Host "  STATUS: DEGRADED" -ForegroundColor Yellow
    Write-SupervisorLog "STATUS result: DEGRADED"
    Write-Host "  STATUS RESULT=DEGRADED"
} else {
    Write-Host "  STATUS: HEALTHY" -ForegroundColor Green
    Write-SupervisorLog "STATUS result: HEALTHY"
    Write-Host "  STATUS RESULT=HEALTHY"
}
Write-Host "========================================"
Write-Host ""

# Exit code for automation
if ($AnyIssues) { exit 1 } else { exit 0 }