$ErrorActionPreference = "Stop"

$files = @(
    "scripts\common.ps1",
    "scripts\engine-health.ps1",
    "scripts\start.ps1",
    "scripts\stop.ps1",
    "scripts\status.ps1",
    "scripts\health.ps1"
)

$allOk = $true

foreach ($f in $files) {
    if (-not (Test-Path $f)) {
        Write-Host "$f MISSING"
        $allOk = $false
        continue
    }

    $fullPath = (Resolve-Path $f).Path
    $tokens = $null
    $errors = $null

    try {
        [System.Management.Automation.Language.Parser]::ParseFile(
            $fullPath,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null

        if ($errors -and $errors.Count -gt 0) {
            Write-Host "$f PARSE_ERRORS: $($errors.Count)"
            foreach ($err in $errors) {
                Write-Host "  Line $($err.Extent.StartLineNumber): $($err.Message)"
            }
            $allOk = $false
        } else {
            Write-Host "$f OK"
        }
    } catch {
        Write-Host "$f EXCEPTION: $($_.Exception.Message)"
        $allOk = $false
    }
}

if ($allOk) {
    Write-Host "ALL SCRIPTS SYNTAX OK"
    exit 0
} else {
    Write-Host "SYNTAX ERRORS FOUND"
    exit 1
}