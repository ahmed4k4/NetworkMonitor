# Engine readiness helpers.
#
# The network engine is a blocking packet-capture process. It has NO HTTP
# endpoint, so `/api/health` (the API's own endpoint) can never be used to
# prove "engine" readiness. The authoritative readiness signal is the engine's
# log: once `start_capture()` runs, the engine writes
#   [INFO] Starting packet capture on <interface> ...   (via logger -> stderr)
# So this helper verifies:
#   1. the process is actually alive, AND
#   2. the log contains the capture-started sentinel.

# Sentinel string emitted by engine.start_capture()
$script:EngineStartupSentinel = "Starting packet capture on"

function Test-EngineLogReady {
    param(
        [string]$LogFile,
        [int]$ProcessId
    )

    # Process alive?
    if ($ProcessId -gt 0) {
        if (-not (Test-ProcessAlive $ProcessId)) {
            Write-SystemLog "engine-health: process $ProcessId is not alive." "WARN"
            return $false
        }
    }

    if ([string]::IsNullOrWhiteSpace($LogFile)) {
        Write-SystemLog "engine-health: no log file specified." "WARN"
        return $false
    }

    if (-not (Test-Path $LogFile)) {
        Write-SystemLog "engine-health: log file '$LogFile' does not exist yet (still booting)." "WARN"
        return $false
    }

    $content = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($content)) {
        Write-SystemLog "engine-health: log file is empty (engine still starting)." "WARN"
        return $false
    }

    if ($content -match [regex]::Escape($script:EngineStartupSentinel)) {
        Write-SystemLog "engine-health: startup sentinel present in '$LogFile'."
        return $true
    }

    Write-SystemLog "engine-health: startup sentinel NOT yet present in '$LogFile'." "WARN"
    return $false
}