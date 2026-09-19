$ErrorActionPreference = "Stop"
$DashboardRoot = "E:\NetworkMonitor\dashboard"
$PidFile = "E:\NetworkMonitor\data\runtime\dashboard.pid"
$OutLog = "E:\NetworkMonitor\logs\dashboard.out.log"
$ErrLog = "E:\NetworkMonitor\logs\dashboard.error.log"

# Ensure npm.cmd and node.exe are resolvable
$nodeDir = "G:\nodejs"
if (Test-Path "$nodeDir\npm.cmd") {
  $env:Path = "$nodeDir;$env:Path"
}

$proc = Start-Process `
  -FilePath "G:\nodejs\npm.cmd" `
  -ArgumentList "run","start" `
  -WorkingDirectory $DashboardRoot `
  -RedirectStandardOutput $OutLog `
  -RedirectStandardError $ErrLog `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $PidFile -Value $proc.Id
Write-Output ("DASHBOARD_PID=" + $proc.Id)