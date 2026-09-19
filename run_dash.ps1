# Run the Next.js dashboard PRODUCTION server directly with visible output.
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$dash = "e:\NetworkMonitor\dashboard"
$out = "e:\NetworkMonitor\logs\dash_direct.out.log"
$err = "e:\NetworkMonitor\logs\dash_direct.err.log"
Remove-Item $out,$err -Force -ErrorAction SilentlyContinue

# Kill anything on 3000 first
$conns = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns) { try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop } catch {} }

Write-Host "=== Running: npm run start (next start) ==="
$p = Start-Process -FilePath "npm.cmd" -ArgumentList "run","start" -WorkingDirectory $dash `
   -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
Write-Host "Launched npm.cmd PID: $($p.Id)"
Start-Sleep -Seconds 12
Write-Host "=== npm.cmd PID alive? $(Test-Path -Path '') / process check ==="
$alive = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
Write-Host "npm.cmd PID $($p.Id) alive: $([bool]$alive)"

# Find any node listening on 3000
$listen = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
Write-Host "=== Listener on :3000 ==="
$listen | ForEach-Object { $op = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "  PID $($_.OwningProcess)  $($op.ProcessName)" }

Write-Host "=== dashboard.error.log tail ==="
Get-Content $err -ErrorAction SilentlyContinue
Write-Host "=== dashboard.out.log tail ==="
Get-Content $out -ErrorAction SilentlyContinue