$ErrorActionPreference = 'SilentlyContinue'

Write-Host "=== PROCESS COMMAND LINE CHECK ==="
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Select-Object ProcessId, CommandLine |
    Format-List |
    Out-String |
    Write-Host
Write-Host "=== DONE ==="