# Run a production build of the Next.js dashboard and capture output.
$ErrorActionPreference = "Continue"
$dash = "e:\NetworkMonitor\dashboard"
$out = "e:\NetworkMonitor\logs\dash_build.out.log"
$err = "e:\NetworkMonitor\logs\dash_build.err.log"
Remove-Item $out,$err -Force -ErrorAction SilentlyContinue
Write-Host "=== npm run build ==="
$p = Start-Process -FilePath "npm.cmd" -ArgumentList "run","build" -WorkingDirectory $dash `
   -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -NoNewWindow
$null = $p.WaitForExit(360000)
Write-Host "build npm.cmd PID $($p.Id) exited with code: $($p.ExitCode)"
Write-Host "=== stdout (stdout.log) ==="
Get-Content $out -ErrorAction SilentlyContinue
Write-Host "=== stderr (error.log) ==="
Get-Content $err -ErrorAction SilentlyContinue
Write-Host "=== top-level BUILD_ID now? ==="
Test-Path "$dash\.next\BUILD_ID"