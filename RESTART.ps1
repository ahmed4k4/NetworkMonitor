$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$Root\STOP.ps1"

Start-Sleep -Seconds 3

& "$Root\START.ps1"