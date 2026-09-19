$ErrorActionPreference = "Continue"

Write-Host "--- Get-Command npm ---"
Get-Command npm -ErrorAction SilentlyContinue | Format-List Name, Source, CommandType

Write-Host "--- Get-Command npm.cmd ---"
Get-Command npm.cmd -ErrorAction SilentlyContinue | Format-List Name, Source, CommandType

Write-Host "--- where.exe npm ---"
where.exe npm 2>&1

Write-Host "--- where.exe npm.cmd ---"
where.exe npm.cmd 2>&1

Write-Host "--- npm path via Get-Command ---"
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npm) {
    Write-Host "npm.cmd source: $($npm.Source)"
    Write-Host "npm.cmd exists: $(Test-Path $npm.Source)"
} else {
    Write-Host "npm.cmd NOT found via Get-Command"
}

Write-Host "--- node/npm versions ---"
node --version 2>&1
npm --version 2>&1