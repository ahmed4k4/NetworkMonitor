$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Require-Administrator

$BackupDir = Join-Path `
    $Root `
    "backups\$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"

New-Item `
    -ItemType Directory `
    -Path $BackupDir `
    -Force | Out-Null


Write-SystemLog `
    "Starting backup."


# Database backup
# سيتم ربطه بـ database/backup.py لاحقًا


# Configuration
Copy-Item `
    "$Root\config" `
    "$BackupDir\config" `
    -Recurse `
    -Force


# Environment
if (Test-Path "$Root\.env") {

    Copy-Item `
        "$Root\.env" `
        "$BackupDir\.env" `
        -Force
}


Write-SystemLog `
    "Backup completed: $BackupDir"