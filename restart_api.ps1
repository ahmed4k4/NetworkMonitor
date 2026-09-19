# Restart the API and capture live logs for the audit.
Set-StrictMode -Off
$ErrorActionPreference = "Continue"

# Kill any process on :8000
$conns = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    $pid2 = $c.OwningProcess
    try { Stop-Process -Id $pid2 -Force -ErrorAction Stop; Write-Host "killed $pid2" } catch { Write-Host "no suproc $pid2" }
}
Start-Sleep -Seconds 2

$py = "e:\NetworkMonitor\network-engine\.venv\Scripts\python.exe"
$wd = "e:\NetworkMonitor\network-engine"
$out = "e:\NetworkMonitor\logs\api_audit.out.log"
$err = "e:\NetworkMonitor\logs\api_audit.err.log"
Remove-Item $out,$err -Force -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath $py -ArgumentList "-m","uvicorn","api.app:app","--host","127.0.0.1","--port","8000","--log-level","info" -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
Write-Host "API started PID $($proc.Id)"
Start-Sleep -Seconds 5
Write-Host "--- ERR ---"
Get-Content $err -ErrorAction SilentlyContinue
Write-Host "--- OUT ---"
Get-Content $out -ErrorAction SilentlyContinue
netstat -ano | findstr :8000