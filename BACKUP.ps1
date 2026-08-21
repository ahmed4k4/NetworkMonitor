$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$Root\scripts\backup.ps1"