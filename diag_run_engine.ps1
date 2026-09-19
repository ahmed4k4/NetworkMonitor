$ErrorActionPreference = "Continue"
$Root = "E:\NetworkMonitor"
$Py = "$Root\.venv\Scripts\python.exe"
$Out = "$Root\logs\engine_manual.out.log"
$Err = "$Root\logs\engine_manual.err.log"

# Ensure logs dir
New-Item -ItemType Directory -Force -Path "$Root\logs" | Out-Null

# Clear old logs
Remove-Item $Out -Force -ErrorAction SilentlyContinue
Remove-Item $Err -Force -ErrorAction SilentlyContinue

Write-Host "Launching engine manually..."
$p = Start-Process `
    -FilePath $Py `
    -ArgumentList "main.py" `
    -WorkingDirectory "$Root\network-engine" `
    -RedirectStandardOutput $Out `
    -RedirectStandardError $Err `
    -PassThru `
    -WindowStyle Hidden

Write-Host "PID=$($p.Id)"
Start-Sleep -Seconds 10

$alive = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
if ($alive) {
    Write-Host "ALIVE=YES"
} else {
    Write-Host "ALIVE=NO"
}

Write-Host "--- STDOUT ---"
if (Test-Path $Out) { Get-Content $Out }
Write-Host "--- STDERR ---"
if (Test-Path $Err) { Get-Content $Err }