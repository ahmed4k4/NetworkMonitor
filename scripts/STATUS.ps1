$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Write-Host ""
Write-Host "========================================"
Write-Host "       NETWORK MONITOR STATUS"
Write-Host "========================================"
Write-Host ""


function Show-ProcessStatus {

    param(
        [string]$Name,
        [string]$PidFile
    )

    if (!(Test-Path $PidFile)) {

        Write-Host "$Name : STOPPED"

        return
    }

    $ProcessId = Get-Content $PidFile

    $Process = Get-Process `
        -Id $ProcessId `
        -ErrorAction SilentlyContinue

    if ($Process) {

        Write-Host "$Name : RUNNING  PID=$ProcessId"

    } else {

        Write-Host "$Name : CRASHED"
    }
}


Show-ProcessStatus `
    "Engine" `
    "$Root\data\runtime\engine.pid"


Show-ProcessStatus `
    "API" `
    "$Root\data\runtime\api.pid"


Show-ProcessStatus `
    "Dashboard" `
    "$Root\data\runtime\dashboard.pid"


Write-Host ""

# PostgreSQL

$Postgres = Get-Service |
    Where-Object {
        $_.Name -like "postgresql*"
    } |
    Select-Object -First 1


if ($Postgres) {

    Write-Host `
        "PostgreSQL : $($Postgres.Status)"

} else {

    Write-Host `
        "PostgreSQL : NOT FOUND"
}


Write-Host ""

# Network

Write-Host "LAN Configuration:"
Write-Host ""

Get-NetIPConfiguration |
    Where-Object {
        $_.InterfaceAlias -eq "Ethernet" -or
        $_.InterfaceAlias -eq "Wi-Fi"
    } |
    Format-Table `
        InterfaceAlias,
        IPv4Address,
        IPv4DefaultGateway `
        -AutoSize


Write-Host ""