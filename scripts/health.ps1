$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"


Write-Host ""
Write-Host "========================================"
Write-Host "       NETWORK MONITOR HEALTH"
Write-Host "========================================"
Write-Host ""


$Healthy = $true


# =====================================
# PostgreSQL
# =====================================

Write-Host "[1] PostgreSQL"

$Postgres = Get-Service |
    Where-Object {
        $_.Name -like "postgresql*"
    } |
    Select-Object -First 1


if ($Postgres -and $Postgres.Status -eq "Running") {

    Write-Host "    [OK] PostgreSQL is running"

} else {

    Write-Host "    [FAIL] PostgreSQL is not running"

    $Healthy = $false
}


# =====================================
# Network Engine Process
# =====================================

Write-Host ""
Write-Host "[2] Network Engine"

$EnginePidFile = Join-Path `
    $Root `
    "data\runtime\engine.pid"


if (Test-Path $EnginePidFile) {

    $EnginePid = Get-Content $EnginePidFile

    $EngineProcess = Get-Process `
        -Id $EnginePid `
        -ErrorAction SilentlyContinue

    if ($EngineProcess) {

        Write-Host `
            "    [OK] Engine is running - PID: $EnginePid"

    } else {

        Write-Host `
            "    [FAIL] Engine process not found"

        $Healthy = $false
    }

} else {

    Write-Host `
        "    [FAIL] Engine PID file not found"

    $Healthy = $false
}


# =====================================
# API
# =====================================

Write-Host ""
Write-Host "[3] API"

if (Test-Port "127.0.0.1" 8000) {

    Write-Host `
        "    [OK] API port 8000 is reachable"

} else {

    Write-Host `
        "    [FAIL] API port 8000 is not reachable"

    $Healthy = $false
}


# =====================================
# Dashboard
# =====================================

Write-Host ""
Write-Host "[4] Dashboard"

if (Test-Port "127.0.0.1" 3000) {

    Write-Host `
        "    [OK] Dashboard port 3000 is reachable"

} else {

    Write-Host `
        "    [FAIL] Dashboard port 3000 is not reachable"

    $Healthy = $false
}


# =====================================
# LAN Interface
# =====================================

Write-Host ""
Write-Host "[5] LAN Interface"

$LAN = Get-NetAdapter |
    Where-Object {
        $_.Name -eq "Ethernet"
    }


if ($LAN -and $LAN.Status -eq "Up") {

    Write-Host `
        "    [OK] Ethernet interface is UP"

} else {

    Write-Host `
        "    [FAIL] Ethernet interface is DOWN"

    $Healthy = $false
}


# =====================================
# LAN IP
# =====================================

Write-Host ""
Write-Host "[6] LAN IP"

$LANIP = Get-NetIPAddress `
    -InterfaceAlias "Ethernet" `
    -AddressFamily IPv4 `
    -ErrorAction SilentlyContinue


if ($LANIP -and $LANIP.IPAddress -eq "192.168.137.1") {

    Write-Host `
        "    [OK] LAN IP: 192.168.137.1"

} else {

    Write-Host `
        "    [WARNING] Expected LAN IP: 192.168.137.1"

    if ($LANIP) {

        Write-Host `
            "    Current IP: $($LANIP.IPAddress)"
    }
}


# =====================================
# Gateway
# =====================================

Write-Host ""
Write-Host "[7] Gateway"

$GatewayTest = Test-Connection `
    -ComputerName "192.168.137.2" `
    -Count 1 `
    -Quiet `
    -ErrorAction SilentlyContinue


if ($GatewayTest) {

    Write-Host `
        "    [OK] Gateway 192.168.137.2 is reachable"

} else {

    Write-Host `
        "    [FAIL] Gateway 192.168.137.2 is unreachable"

    $Healthy = $false
}


# =====================================
# Internet
# =====================================

Write-Host ""
Write-Host "[8] Internet"

$InternetTest = Test-Connection `
    -ComputerName "8.8.8.8" `
    -Count 1 `
    -Quiet `
    -ErrorAction SilentlyContinue


if ($InternetTest) {

    Write-Host `
        "    [OK] Internet connectivity"

} else {

    Write-Host `
        "    [FAIL] Internet connectivity"

    $Healthy = $false
}


# =====================================
# Final Result
# =====================================

Write-Host ""
Write-Host "========================================"

if ($Healthy) {

    Write-Host "        SYSTEM HEALTHY"

} else {

    Write-Host "        SYSTEM HAS PROBLEMS"
}

Write-Host "========================================"
Write-Host ""


if ($Healthy) {

    exit 0

} else {

    exit 1
}