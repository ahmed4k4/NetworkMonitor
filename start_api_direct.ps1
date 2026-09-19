$python = 'e:\NetworkMonitor\.venv\Scripts\python.exe'
$wd = 'e:\NetworkMonitor\network-engine'
$out = 'e:\NetworkMonitor\logs\api_direct.log'
$err = 'e:\NetworkMonitor\logs\api_direct.err.log'
$pidFile = 'e:\NetworkMonitor\logs\api_direct.pid'

# Kill any existing on port 8000 handled separately
$p = Start-Process -FilePath $python `
    -ArgumentList '-m','uvicorn','api.app:app','--host','127.0.0.1','--port','8000','--log-level','info' `
    -WorkingDirectory $wd `
    -RedirectStandardOutput $out `
    -RedirectStandardError $err `
    -PassThru
$p.Id | Set-Content $pidFile -Force
Write-Output ("API started PID: " + $p.Id)