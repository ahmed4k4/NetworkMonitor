$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Require-Administrator

$Timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$BackupDir = Join-Path $Root "backups\$Timestamp"

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

Write-SystemLog "Starting backup: $Timestamp"

$OverallSuccess = $true

# =====================================
# 1. Database backup (using pg_dump)
# =====================================
Write-SystemLog "Backing up database..."

$DbBackupFile = Join-Path $BackupDir "database.sql"
$pgDumpPath = "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"  # Adjust version as needed

if (Test-Path $pgDumpPath) {
    $env:PGPASSWORD = "postgres"
    $result = & $pgDumpPath `
        -h localhost `
        -p 5432 `
        -U postgres `
        -d network_monitor `
        -f $DbBackupFile `
        --no-password `
        --verbose 2>&1

    if ($LASTEXITCODE -eq 0 -and (Test-Path $DbBackupFile)) {
        $size = (Get-Item $DbBackupFile).Length
        Write-SystemLog "Database backup completed: $size bytes"
    } else {
        Write-SystemLog "Database backup failed" "ERROR"
        $OverallSuccess = $false
    }
} else {
    Write-SystemLog "pg_dump not found at $pgDumpPath, skipping database backup" "WARN"
}

# =====================================
# 2. Configuration
# =====================================
Write-SystemLog "Backing up configuration..."

try {
    Copy-Item `
        (Join-Path $Root "config") `
        (Join-Path $BackupDir "config") `
        -Recurse -Force
    Write-SystemLog "Configuration backed up"
} catch {
    Write-SystemLog "Configuration backup failed: $($_.Exception.Message)" "ERROR"
    $OverallSuccess = $false
}

# =====================================
# 3. Environment files
# =====================================
Write-SystemLog "Backing up environment files..."

$envFiles = @(".env", "network-engine\.env")
foreach ($envFile in $envFiles) {
    $src = Join-Path $Root $envFile
    if (Test-Path $src) {
        $dest = Join-Path $BackupDir $envFile
        Copy-Item $src $dest -Force
    }
}

# =====================================
# 4. Runtime data (PID files, etc.)
# =====================================
Write-SystemLog "Backing up runtime data..."

try {
    Copy-Item `
        (Join-Path $Root "data\runtime") `
        (Join-Path $BackupDir "runtime") `
        -Recurse -Force -ErrorAction SilentlyContinue
} catch { }

# =====================================
# 5. Logs (last 1000 lines each)
# =====================================
Write-SystemLog "Backing up recent logs..."

$logBackupDir = Join-Path $BackupDir "logs"
New-Item -ItemType Directory -Path $logBackupDir -Force | Out-Null

$logFiles = Get-ChildItem (Join-Path $Root "logs") -Filter "*.log" -ErrorAction SilentlyContinue
foreach ($logFile in $logFiles) {
    $outFile = Join-Path $logBackupDir $logFile.Name
    Get-Content $logFile.FullName -Tail 1000 | Set-Content $outFile
}

# =====================================
# 6. Create manifest
# =====================================
Write-SystemLog "Creating backup manifest..."

$manifest = @{
    timestamp = $Timestamp
    version = "1.0"
    components = @(
        @{ name = "database"; file = "database.sql"; required = $true },
        @{ name = "config"; file = "config"; required = $true },
        @{ name = "environment"; file = ".env"; required = $false },
        @{ name = "runtime"; file = "runtime"; required = $false },
        @{ name = "logs"; file = "logs"; required = $false }
    )
}

$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $BackupDir "manifest.json")

# =====================================
# 7. Verify backup
# =====================================
Write-SystemLog "Verifying backup..."

$verified = $true
if (Test-Path $DbBackupFile) {
    $dbSize = (Get-Item $DbBackupFile).Length
    if ($dbSize -lt 100) {  # Less than 100 bytes is suspicious
        Write-SystemLog "Database backup appears empty" "WARN"
        $verified = $false
    }
}

if (Test-Path (Join-Path $BackupDir "config")) {
    Write-SystemLog "Config backup verified"
} else {
    Write-SystemLog "Config backup missing" "ERROR"
    $verified = $false
}

# =====================================
# 8. Create checksums
# =====================================
Write-SystemLog "Creating checksums..."

$checksums = @{}
Get-ChildItem $BackupDir -File -Recurse | ForEach-Object {
    $hash = Get-FileHash $_.FullName -Algorithm SHA256
    $relPath = $_.FullName.Substring($BackupDir.Length + 1)
    $checksums[$relPath] = $hash.Hash
}
$checksums | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $BackupDir "checksums.json")

# =====================================
# Summary
# =====================================
Write-SystemLog "============================================"
if ($OverallSuccess -and $verified) {
    Write-SystemLog "Backup completed successfully: $BackupDir"
    Write-Host "Backup location: $BackupDir"
    exit 0
} else {
    Write-SystemLog "Backup completed with warnings/errors" "WARN"
    Write-Host "Backup location: $BackupDir (check logs)"
    exit 1
}
