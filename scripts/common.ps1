$ProjectRoot = Split-Path -Parent $PSScriptRoot

$EngineRoot = Join-Path $ProjectRoot "network-engine"
$DashboardRoot = Join-Path $ProjectRoot "dashboard"

$LogDirectory = Join-Path $ProjectRoot "logs"
$RuntimeDirectory = Join-Path $ProjectRoot "data\runtime"

New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeDirectory | Out-Null


function Write-SystemLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    $Line = "[$Time] [$Level] $Message"

    Write-Host $Line

    Add-Content `
        -Path (Join-Path $LogDirectory "system.log") `
        -Value $Line
}


function Test-Administrator {

    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()

    $Principal = New-Object `
        Security.Principal.WindowsPrincipal($Identity)

    return $Principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}


function Require-Administrator {

    if (!(Test-Administrator)) {

        Write-SystemLog `
            "Administrator privileges required." `
            "ERROR"

        exit 1
    }
}


function Test-CommandExists {

    param(
        [string]$Command
    )

    return $null -ne (
        Get-Command $Command `
            -ErrorAction SilentlyContinue
    )
}


function Test-Port {
    param (
        [string]$TargetHost = "127.0.0.1",
        [int]$Port
    )
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $tcp.BeginConnect($TargetHost, $Port, $null, $null)
        if ($async.AsyncWaitHandle.WaitOne(500, $false)) {
            $tcp.EndConnect($async)
            $tcp.Close()
            return $true
        }
        $tcp.Close()
        return $false
    } catch {
        return $false
    }
}