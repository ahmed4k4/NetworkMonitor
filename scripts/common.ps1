# ---------------------------------------------------------------------------
# NetworkMonitor - canonical shared lifecycle module.
# This is the SINGLE source of truth for process/port/config/health helpers.
# No other script may re-implement these helpers.
# ---------------------------------------------------------------------------

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$EngineRoot = Join-Path $ProjectRoot "network-engine"
$DashboardRoot = Join-Path $ProjectRoot "dashboard"

$LogDirectory = Join-Path $ProjectRoot "logs"
$RuntimeDirectory = Join-Path $ProjectRoot "data\runtime"
$ConfigDirectory = Join-Path $ProjectRoot "config"

New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $ConfigDirectory | Out-Null

# Service definitions used across start/stop/status/health. Single source of truth.
#   Name      : human label
#   Key       : runtime pid-file basename (engine.pid / api.pid / dashboard.pid)
#   Process   : executable image name(s) to verify PID ownership (no .exe)
#   Ports     : TCP ports this service owns (must be closed after stop)
#   Url       : HTTP health URL (null = log-based only)
$script:ServiceDefinitions = @(
    @{
        Name      = "Network Engine"
        Key       = "engine"
        Process   = @("python", "pythonw")
        Ports     = @()
        Url       = $null
        PidFile   = Join-Path $RuntimeDirectory "engine.pid"
        OutLog    = Join-Path $LogDirectory "engine.out.log"
        ErrLog    = Join-Path $LogDirectory "engine.error.log"
    },
    @{
        Name      = "API"
        Key       = "api"
        Process   = @("python", "pythonw")
        Ports     = @(8000)
        Url       = "http://127.0.0.1:8000/api/health"
        PidFile   = Join-Path $RuntimeDirectory "api.pid"
        OutLog    = Join-Path $LogDirectory "api.out.log"
        ErrLog    = Join-Path $LogDirectory "api.error.log"
    },
    @{
        Name      = "Dashboard"
        Key       = "dashboard"
        Process   = @("node", "npm", "cmd")
        Ports     = @(3000)
        Url       = "http://127.0.0.1:3000/"
        PidFile   = Join-Path $RuntimeDirectory "dashboard.pid"
        OutLog    = Join-Path $LogDirectory "dashboard.out.log"
        ErrLog    = Join-Path $LogDirectory "dashboard.error.log"
    }
)

function Get-ServiceDefinition {
    param([string]$Key)
    return $script:ServiceDefinitions | Where-Object { $_.Key -eq $Key } | Select-Object -First 1
}

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($ProjectRoot) -or -not (Test-Path $EngineRoot)) {
    throw "common.ps1: invalid ProjectRoot '$ProjectRoot' (EngineRoot '$EngineRoot' not found)."
}

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
function Write-SystemLog {
    param([string]$Message, [string]$Level = "INFO")
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Time] [$Level] $Message"
    Write-Host $Line
    Add-Content -Path (Join-Path $LogDirectory "system.log") -Value $Line
}

function Write-ErrorLog {
    param([string]$Message)
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Time] [ERROR] $Message"
    Write-Host $Line -ForegroundColor Red
    Add-Content -Path (Join-Path $LogDirectory "supervisor.log") -Value $Line
}

function Write-SupervisorLog {
    param([string]$Message)
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Time] [SUPERVISOR] $Message"
    Add-Content -Path (Join-Path $LogDirectory "supervisor.log") -Value $Line
}

# ---------------------------------------------------------------------------
# Admin / command helpers
# ---------------------------------------------------------------------------
function Test-Administrator {
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = New-Object Security.Principal.WindowsPrincipal($Identity)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Require-Administrator {
    if (!(Test-Administrator)) {
        Write-SystemLog "Administrator privileges required." "ERROR"
        exit 1
    }
}

function Test-CommandExists {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# ---------------------------------------------------------------------------
# Minimal YAML parser for our simple two-level system.yaml.
# Supports: top-level keys, second-level keys, string / integer scalars,
# inline scalar arrays (`- "x"`), and comments. No anchors or flow maps.
# Returns a PSCustomObject tree so property access works naturally
# ($config.network.lan_interface). PowerShell 5.1 has no built-in YAML.
# ---------------------------------------------------------------------------
function ConvertFrom-SimpleYaml {
    param([string]$Text)

    $root = [ordered]@{}
    $currentTop = $null

    $lines = $Text -split "`r?`n"

    foreach ($raw in $lines) {
        $line = $raw.TrimEnd()
        # Strip comments (not inside quotes; our config has none)
        $hash = $line.IndexOf('#')
        if ($hash -ge 0) { $line = $line.Substring(0, $hash) }
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        if ($line -match '^[A-Za-z0-9_]+\s*:\s*$') {
            # Top-level key with empty value -> dict
            $key = ($line -split ':')[0].Trim()
            $root[$key] = [ordered]@{}
            $currentTop = $key
            continue
        }

        if ($line -match '^\s{2,}') {
            # Second-level entry under currentTop
            if (-not $currentTop) { continue }
            $trimmed = $line.TrimStart()

            if ($trimmed -match '^-\s*(.*)$') {
                # Array item: directly under a top-level list OR under the
                # last second-level key.
                $item = $matches[1].Trim()
                $item = $item -replace '^"|"$|^\x27|\x27$', ''
                # Unescape YAML double-backslash (Windows paths)
                $item = $item -replace '\\\\', '\'
                if ($item -match '^\d+$') { $itemParsed = [long]$item } else { $itemParsed = $item }

                $sub = $root[$currentTop]

                if ($sub -is [System.Collections.IDictionary]) {
                    $isEmptyDict = ($sub.Count -eq 0)
                    if ($isEmptyDict) {
                        # Top-level list first item (e.g. dns_servers:)
                        $root[$currentTop] = @($itemParsed)
                    } else {
                        # Nested list under the last second-level key
                        $last = @($sub.Keys)[-1]
                        $existing = $sub[$last]
                        if ($existing -is [System.Collections.IList] -or $existing -is [object[]]) {
                            $sub[$last] = @($existing) + @($itemParsed)
                        } else {
                            $sub[$last] = @($itemParsed)
                        }
                    }
                }
                elseif ($null -eq $sub -or $sub -is [System.Collections.IList] -or $sub -is [object[]]) {
                    # Top-level list continuation
                    $root[$currentTop] = @($sub) + @($itemParsed)
                }
                continue
            }

            if ($trimmed -match '^([A-Za-z0-9_]+)\s*:\s*(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                $value = $value -replace '^"|"$|^\x27|\x27$', ''
                $value = $value -replace '\\\\', '\'
                if ($value -match '^\d+$') { $parsed = [long]$value }
                elseif ($value -ieq 'true') { $parsed = $true }
                elseif ($value -ieq 'false') { $parsed = $false }
                elseif ($value -ieq 'null' -or $value -eq '~') { $parsed = $null }
                else { $parsed = $value }
                $root[$currentTop][$key] = $parsed
                continue
            }
        }

        # Top-level scalar key
        if ($line -match '^([A-Za-z0-9_]+)\s*:\s*(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $value = $value -replace '^"|"$|^\x27|\x27$', ''
            $value = $value -replace '\\\\', '\'
            if ($value -match '^\d+$') { $parsed = [long]$value }
            elseif ($value -ieq 'true') { $parsed = $true }
            elseif ($value -ieq 'false') { $parsed = $false }
            elseif ($value -ieq 'null' -or $value -eq '~') { $parsed = $null }
            else { $parsed = $value }
            $root[$key] = $parsed
            $currentTop = $null
            continue
        }
    }

    return ConvertTo-NestedObject -InputObject $root
}

# Recursively convert OrderedDictionary -> PSCustomObject (and arrays of them)
# so that $config.network.lan_ip style access works in PowerShell 5.1.
function ConvertTo-NestedObject {
    param($InputObject)

    if ($null -eq $InputObject) { return $null }

    if ($InputObject -is [System.Collections.IDictionary]) {
        $obj = New-Object -TypeName PSObject
        foreach ($k in $InputObject.Keys) {
            $value = ConvertTo-NestedObject -InputObject $InputObject[$k]
            $obj | Add-Member -MemberType NoteProperty -Name $k -Value $value
        }
        return $obj
    }

    if ($InputObject -is [System.Collections.IList] -or $InputObject -is [object[]]) {
        $out = @()
        foreach ($item in $InputObject) {
            $out += ConvertTo-NestedObject -InputObject $item
        }
        return $out
    }

    return $InputObject
}

# ---------------------------------------------------------------------------
# Configuration read
# ---------------------------------------------------------------------------
function Read-Config {
    param([string]$Key, [string]$Default = "")

    $configFile = Join-Path $ConfigDirectory "system.yaml"
    if (-not (Test-Path $configFile)) {
        throw "Read-Config: config file '$configFile' does not exist."
    }

    try {
        $config = ConvertFrom-SimpleYaml -Text (Get-Content $configFile -Raw)
    } catch {
        throw "Read-Config: failed to parse '$configFile': $($_.Exception.Message)"
    }

    if ($null -ne $config -and $null -ne $config.$Key) {
        return $config.$Key
    }
    return $Default
}

# ---------------------------------------------------------------------------
# Config constants (single source)
# ---------------------------------------------------------------------------
$script:Config = $null
try {
    $cfgFile = Join-Path $ConfigDirectory "system.yaml"
    if (Test-Path $cfgFile) {
        $script:Config = ConvertFrom-SimpleYaml -Text (Get-Content $cfgFile -Raw)
    }
} catch {
    Write-Host "WARN: could not parse system.yaml: $($_.Exception.Message)" -ForegroundColor Yellow
}

$script:DBHost     = if ($script:Config -and $script:Config.database.host) { $script:Config.database.host } else { "127.0.0.1" }
$script:DBPort     = if ($script:Config -and $script:Config.database.port) { [int]$script:Config.database.port } else { 5432 }
$script:DBName     = if ($script:Config -and $script:Config.database.name) { $script:Config.database.name } else { "network_control" }
$script:DBUser     = if ($script:Config -and $script:Config.database.user) { $script:Config.database.user } else { "postgres" }
$script:DBPassword = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "12345678" }

$script:LanInterface = if ($script:Config -and $script:Config.network.lan_interface) { $script:Config.network.lan_interface } else { "Ethernet" }
$script:LanIP        = if ($script:Config -and $script:Config.network.lan_ip) { $script:Config.network.lan_ip } else { "192.168.137.1" }
$script:GatewayIP    = if ($script:Config -and $script:Config.network.upstream_gateway) { $script:Config.network.upstream_gateway } else { "192.168.137.2" }

# ---------------------------------------------------------------------------
# Port / HTTP helpers
# ---------------------------------------------------------------------------
function Test-Port {
    param (
        [string]$TargetHost = "127.0.0.1",
        [int]$Port,
        [int]$TimeoutMs = 2000
    )

    if ($Port -lt 1 -or $Port -gt 65535) {
        throw "Test-Port: invalid port '$Port'"
    }

    $tcp = $null
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect($TargetHost, $Port, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        if ($wait) {
            $tcp.EndConnect($connect)
            $tcp.Close()
            return $true
        }
        $tcp.Close()
        return $false
    } catch {
        if ($tcp) { try { $tcp.Close() } catch { } }
        return $false
    }
}

function Test-HTTP {
    param (
        [string]$Url,
        [int]$TimeoutMs = 5000,
        [int[]]$ExpectedStatus = @(200)
    )

    if ([string]::IsNullOrWhiteSpace($Url)) {
        throw "Test-HTTP: Url is required"
    }

    try {
        $request = [System.Net.HttpWebRequest]::Create($Url)
        $request.Timeout = $TimeoutMs
        $request.Method = "GET"
        $request.AllowAutoRedirect = $false
        $response = $request.GetResponse()
        $statusCode = [int]$response.StatusCode
        $response.Close()
        return $ExpectedStatus -contains $statusCode
    } catch {
        $exception = $_.Exception
        if ($exception) {
            while ($null -ne $exception.InnerException) {
                $exception = $exception.InnerException
            }
            if ($exception -and $exception.Response) {
                $statusCode = [int]$exception.Response.StatusCode
                return $ExpectedStatus -contains $statusCode
            }
        }
        return $false
    }
}

# Dashboard readiness: a real HTTP server must be answering on the listen port.
# Accepts any 1xx/2xx/3xx/401 as "alive" (next start can 307-redirect /).
function Test-DashReady {
    param (
        [string]$Hostname = "127.0.0.1",
        [int]$Port = 3000,
        [int]$TimeoutMs = 3000
    )

    if (-not (Test-Port $Hostname $Port $TimeoutMs)) {
        return $false
    }

    $baseUrl = "http://${Hostname}:${Port}/"
    try {
        $req = [System.Net.HttpWebRequest]::Create($baseUrl)
        $req.Timeout = $TimeoutMs
        $req.Method = "GET"
        $req.AllowAutoRedirect = $false
        try {
            $resp = $req.GetResponse()
            $code = [int]$resp.StatusCode
            $resp.Close()
            return ($code -ge 100 -and $code -lt 500)
        } catch {
            $webEx = $_.Exception
            while ($null -ne $webEx.InnerException) { $webEx = $webEx.InnerException }
            if ($webEx -and $webEx.Response) {
                $code = [int]$webEx.Response.StatusCode
                return ($code -ge 100 -and $code -lt 500)
            }
            return $false
        }
    } catch {
        return $false
    }
}

# ---------------------------------------------------------------------------
# PostgreSQL check (uses psql when available, otherwise TCP only)
# ---------------------------------------------------------------------------
function Test-PostgreSQL {
    param(
        [string]$ConnectionString = ""
    )

    try {
        if (Test-CommandExists "psql") {
            $env:PGPASSWORD = $script:DBPassword
            $result = & psql `
                -h $script:DBHost `
                -p $script:DBPort `
                -U $script:DBUser `
                -d $script:DBName `
                -t -A -c "SELECT 1" 2>$null
            return ($result -eq "1")
        }
        # Fallback: verify TCP port only (we cannot prove auth without psql)
        return Test-Port "127.0.0.1" ([int]$script:DBPort) 3000
    } catch {
        return $false
    }
}

# ---------------------------------------------------------------------------
# PID helpers
# ---------------------------------------------------------------------------
function Get-ProcessIdFromFile {
    param([string]$PidFilePath)

    if ([string]::IsNullOrWhiteSpace($PidFilePath)) {
        throw "Get-ProcessIdFromFile: PidFilePath is required"
    }

    if (!(Test-Path $PidFilePath)) {
        return $null
    }

    $content = Get-Content $PidFilePath -ErrorAction Stop
    if ($content -and $content -match '^\d+$') {
        return [int]($content.Trim())
    }

    throw "Get-ProcessIdFromFile: PID file '$PidFilePath' is corrupt (expected a single integer)."
}

function Test-ProcessAlive {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $false }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    return $null -ne $proc
}

# Verify a PID exists AND its image name is one of the expected images.
# Prevents treating a recycled PID (now a different program) as "our" service.
function Test-PidOwner {
    param(
        [int]$ProcessId,
        [string[]]$ExpectedNames
    )
    if ($ProcessId -le 0) { return $false }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $false }
    foreach ($name in $ExpectedNames) {
        if ($proc.ProcessName -ieq $name) { return $true }
    }
    return $false
}

# ---------------------------------------------------------------------------
# Process tree helpers (child-process-aware)
# ---------------------------------------------------------------------------

# Return the full descendant process tree (recursively) rooted at a PID,
# INCLUDING the root itself. Uses CIM Win32_Process ParentProcessId.
function Get-ProcessTreeIds {
    param(
        [int]$RootProcessId
    )

    $ids = @()
    if ($RootProcessId -le 0) { return $ids }

    try {
        $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Select-Object ProcessId, ParentProcessId
    } catch {
        $procs = @()
    }

    $childrenByParent = @{}
    foreach ($p in $procs) {
        if ($null -eq $p.ParentProcessId) { continue }
        $parentId = [int]$p.ParentProcessId
        if (-not $childrenByParent.ContainsKey($parentId)) {
            $childrenByParent[$parentId] = @()
        }
        $childrenByParent[$parentId] += [int]$p.ProcessId
    }

    # BFS
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue([int]$RootProcessId)
    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        if ($ids -contains $current) { continue }
        $ids += $current
        if ($childrenByParent.ContainsKey($current)) {
            foreach ($child in $childrenByParent[$current]) {
                $queue.Enqueue([int]$child)
            }
        }
    }

    return $ids
}

# Kill a process and ALL of its descendants. Returns $true when every tracked
# PID is confirmed gone.
function Stop-ProcessTree {
    param(
        [string]$Name,
        [int]$RootProcessId,
        [int]$GracefulTimeout = 8,
        [int]$ForceTimeout = 3
    )

    if ($RootProcessId -le 0) { return $true }

    $treeIds = Get-ProcessTreeIds -RootProcessId $RootProcessId
    Write-SystemLog ("{0}: process tree PIDs: {1}" -f $Name, ($treeIds -join ', '))

    # Graceful phase: CloseMainWindow for GUI-capable roots, then wait.
    $root = Get-Process -Id $RootProcessId -ErrorAction SilentlyContinue
    if ($root) {
        try { $root.CloseMainWindow() | Out-Null } catch { }
    }

    $waited = 0
    while ($waited -lt $GracefulTimeout) {
        $alive = @($treeIds | Where-Object { Test-ProcessAlive $_ })
        if ($alive.Count -eq 0) {
            Write-SystemLog "$Name tree terminated gracefully."
            return $true
        }
        Start-Sleep -Seconds 1
        $waited++
    }

    # Force phase: kill remaining tree members (children first, then root).
    Write-SystemLog "$Name tree did not stop gracefully; forcing." "WARN"
    $alive = @($treeIds | Where-Object { Test-ProcessAlive $_ })
    $alive = @($alive | Sort-Object { if ($_ -eq $RootProcessId) { 1 } else { 0 } })
    foreach ($pidId in $alive) {
        if (-not (Test-ProcessAlive $pidId)) { continue }
        try {
            Stop-Process -Id $pidId -Force -ErrorAction Stop
        } catch {
            # Process may have exited between check and kill -- not fatal.
        }
    }

    Start-Sleep -Seconds $ForceTimeout

    # Re-discover any new descendants spawned during kill and force them too.
    $treeIds2 = Get-ProcessTreeIds -RootProcessId $RootProcessId
    $remaining = @($treeIds2 | Where-Object { Test-ProcessAlive $_ })
    if ($remaining.Count -gt 0) {
        Write-SystemLog ("{0} still has PIDs: {1} after force kill." -f $Name, ($remaining -join ', ')) "ERROR"
        return $false
    }

    Write-SystemLog "$Name tree terminated (forced)."
    return $true
}

# ---------------------------------------------------------------------------
# Service process start with truthful health verification.
# ---------------------------------------------------------------------------
function Start-ServiceProcess {
    param (
        [string]$Name,
        [string]$Executable,
        [string]$Arguments = "",
        [string]$WorkingDirectory,
        [string]$StdOutLog = "",
        [string]$StdErrLog = "",
        [string]$PidFile,
        [scriptblock]$HealthCheck = $null,
        [int]$HealthCheckTimeout = 120
    )

    Write-SystemLog "Starting $Name..."

    if ([string]::IsNullOrWhiteSpace($Executable) -or -not (Test-Path $Executable)) {
        Write-ErrorLog "Start-ServiceProcess($Name): executable not found: '$Executable'"
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    if ([string]::IsNullOrWhiteSpace($WorkingDirectory) -or -not (Test-Path $WorkingDirectory)) {
        Write-ErrorLog "Start-ServiceProcess($Name): working directory not found: '$WorkingDirectory'"
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    if ([string]::IsNullOrWhiteSpace($PidFile)) {
        Write-ErrorLog "Start-ServiceProcess($Name): PidFile is required"
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    # Detect + clear a stale PID file before launching (never trust it blind).
    try {
        $staleId = Get-ProcessIdFromFile -PidFilePath $PidFile -ErrorAction SilentlyContinue
        if ($staleId -and -not (Test-ProcessAlive $staleId)) {
            Write-SystemLog ("{0}: stale PID file '{1}' (PID {2} not alive) removing." -f $Name, $PidFile, $staleId) "WARN"
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Write-SystemLog ("{0}: corrupt PID file '{1}' removing." -f $Name, $PidFile) "WARN"
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }

    $argArray = @()
    if ($Arguments -is [string]) {
        if (-not [string]::IsNullOrWhiteSpace($Arguments)) {
            $argArray = $Arguments -split '\s+'
        }
    } else {
        $argArray = @($Arguments)
    }
    $argArray = @($argArray | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

    if ($argArray.Count -eq 0) {
        Write-ErrorLog "Start-ServiceProcess($Name): no launch arguments supplied"
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    if ([string]::IsNullOrWhiteSpace($StdOutLog)) {
        $StdOutLog = Join-Path $LogDirectory ("{0}.out.log" -f ($Name -replace '[^a-zA-Z0-9.]', '_'))
    }
    if ([string]::IsNullOrWhiteSpace($StdErrLog)) {
        $StdErrLog = Join-Path $LogDirectory ("{0}.error.log" -f ($Name -replace '[^a-zA-Z0-9.]', '_'))
    }
    $process = $null
    try {
        $process = Start-Process `
            -FilePath $Executable `
            -ArgumentList $argArray `
            -WorkingDirectory $WorkingDirectory `
            -RedirectStandardOutput $StdOutLog `
            -RedirectStandardError $StdErrLog `
            -PassThru `
            -WindowStyle Hidden
    } catch {
        Write-ErrorLog "Start-ServiceProcess($Name): failed to launch: $($_.Exception.Message)"
        if (Test-Path $PidFile) { Remove-Item $PidFile -Force -ErrorAction SilentlyContinue }
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    if (-not $process -or $process.Id -le 0) {
        Write-ErrorLog "Start-ServiceProcess($Name): process was not started (no PID)."
        if (Test-Path $PidFile) { Remove-Item $PidFile -Force -ErrorAction SilentlyContinue }
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    $pidValue = $process.Id
    Write-SystemLog "$Name launched with PID: $pidValue"

    # Health verification
    $healthy = $false
    if ($HealthCheck) {
        $startedAt = Get-Date
        $consecutivePasses = 0
        $requiredPasses = 2

        while (($(Get-Date) - $startedAt).TotalSeconds -lt $HealthCheckTimeout) {
            if (-not (Test-ProcessAlive $pidValue)) {
                Write-ErrorLog "Start-ServiceProcess($Name): process (PID $pidValue) exited before health check passed."
                break
            }

            $ok = $false
            try {
                $ok = & $HealthCheck $pidValue
            } catch {
                $ok = $false
                Write-SystemLog "$Name health probe raised: $($_.Exception.Message)" "WARN"
            }

            if ($ok) {
                $consecutivePasses++
                if ($consecutivePasses -ge $requiredPasses) {
                    $healthy = $true
                    break
                }
            } else {
                $consecutivePasses = 0
            }

            Start-Sleep -Seconds 1
        }
    } else {
        Start-Sleep -Seconds 3
        if (Test-ProcessAlive $pidValue) {
            $healthy = $true
        } else {
            Write-ErrorLog "Start-ServiceProcess($Name): process (PID $pidValue) exited shortly after launch."
        }
    }

    if (-not $healthy) {
        Write-SystemLog ("{0} health check failed after {1}s." -f $Name, $HealthCheckTimeout) "ERROR"
        Write-SupervisorLog "$Name health check FAILED (PID $pidValue)."
        Stop-ProcessTree $Name $pidValue -GracefulTimeout 3 -ForceTimeout 2 | Out-Null
        if (Test-Path $PidFile) { Remove-Item $PidFile -Force -ErrorAction SilentlyContinue }
        Write-Host "$Name RESULT=FAILED"
        return $false
    }

    try {
        $pidValue | Set-Content $PidFile -Force
        Write-SystemLog "$Name is healthy. PID file written: $PidFile"
        Write-SupervisorLog "$Name STARTED (PID $pidValue) - health verified."
        Write-Host "$Name RESULT=STARTED"
        return $true
    } catch {
        Write-ErrorLog "Start-ServiceProcess($Name): could not write PID file '$PidFile': $($_.Exception.Message)"
        Stop-ProcessTree $Name $pidValue -GracefulTimeout 3 -ForceTimeout 2 | Out-Null
        Write-Host "$Name RESULT=FAILED"
        return $false
    }
}