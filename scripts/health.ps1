$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"
. "$PSScriptRoot\engine-health.ps1"

# Load configuration (minimal YAML parser from common.ps1)
$configFile = Join-Path $Root "config\system.yaml"
$Config = $null
if (Test-Path $configFile) {
    try {
        $Config = ConvertFrom-SimpleYaml -Text (Get-Content $configFile -Raw)
    } catch {
        Write-ErrorLog "Failed to parse system.yaml: $($_.Exception.Message)"
    }
}

$NetworkConfig = $Config.network
$GatewayIP = if ($NetworkConfig.upstream_gateway) { $NetworkConfig.upstream_gateway } else { "192.168.137.2" }
$LanIP = if ($NetworkConfig.lan_ip) { $NetworkConfig.lan_ip } else { "192.168.137.1" }
$LanInterface = if ($NetworkConfig.lan_interface) { $NetworkConfig.lan_interface } else { "Ethernet" }
$DnsServers = if ($Config.dns_servers) { $Config.dns_servers } else { @("8.8.8.8", "1.1.1.1") }
$InternetTestHosts = if ($Config.internet_test_hosts) { $Config.internet_test_hosts } else { @("8.8.8.8", "1.1.1.1", "cloudflare.com") }

Write-Host ""
Write-Host "========================================"
Write-Host "       NETWORK MONITOR HEALTH CHECK"
Write-Host "========================================"
Write-Host ""

$script:Healthy = $true
$script:Checks = @()

function Add-Check {
    param (
        [string]$Name,
        [bool]$Passed,
        [string]$Detail = "",
        [string]$Level = "FAIL"  # FAIL, WARN, OK
    )
    $script:Checks += [PSCustomObject]@{
        Name = $Name
        Passed = $Passed
        Detail = $Detail
        Level = $Level
    }
    if (-not $Passed -and $Level -eq "FAIL") {
        $script:Healthy = $false
    }
}

# =====================================
# 1. PostgreSQL
# =====================================
Write-Host "PostgreSQL:"
$pgHealthy = $false
try {
    $pgHealthy = Test-PostgreSQL
} catch {
    Write-ErrorLog "PostgreSQL check raised an exception: $($_.Exception.Message)"
}
Add-Check "PostgreSQL Service" $pgHealthy
if ($pgHealthy) { Write-Host "  [OK] PostgreSQL is healthy" -ForegroundColor Green }
else { Write-Host "  [FAIL] PostgreSQL is not healthy" -ForegroundColor Red }

# =====================================
# 2. Network Engine Process
# =====================================
Write-Host ""
Write-Host "Network Engine:"
$enginePidFile = Join-Path $Root "data\runtime\engine.pid"
$enginePid = $null
$engineRunning = $false
try {
    $enginePid = Get-ProcessIdFromFile -PidFilePath $enginePidFile
} catch {
    Write-ErrorLog "Engine PID file issue: $($_.Exception.Message)"
}
if ($enginePid) {
    $engineRunning = Test-ProcessAlive $enginePid
}

# If PID file exists but process is dead, clean it up
if ($enginePid -and -not $engineRunning) {
    Write-Host "  [WARN] Stale PID file found (PID: $enginePid), cleaning up" -ForegroundColor Yellow
    Remove-Item $enginePidFile -Force -ErrorAction SilentlyContinue
    $engineRunning = $false
}

Add-Check "Engine Process" $engineRunning
if ($engineRunning) { Write-Host "  [OK] Engine running (PID: $enginePid)" -ForegroundColor Green }
else { Write-Host "  [FAIL] Engine not running" -ForegroundColor Red }

# Engine readiness: log sentinel + process alive (NOT /api/health, which is API-only)
if ($engineRunning) {
    $engineErrLog = Join-Path $Root "logs\engine.error.log"
    $engineLogReady = Test-EngineLogReady -LogFile $engineErrLog -ProcessId $enginePid
    Add-Check "Engine Capture Started (log sentinel)" $engineLogReady
    if ($engineLogReady) { Write-Host "  [OK] Engine capture started (log sentinel found)" -ForegroundColor Green }
    else { Write-Host "  [WARN] Engine process alive but capture not started (no log sentinel)" -ForegroundColor Yellow }
}

# =====================================
# 3. API
# =====================================
Write-Host ""
Write-Host "API:"
$apiPidFile = Join-Path $Root "data\runtime\api.pid"
$apiPid = $null
$apiRunning = $false
try {
    $apiPid = Get-ProcessIdFromFile -PidFilePath $apiPidFile
} catch {
    Write-ErrorLog "API PID file issue: $($_.Exception.Message)"
}
if ($apiPid) {
    $apiRunning = Test-ProcessAlive $apiPid
}

# If PID file exists but process is dead, clean it up
if ($apiPid -and -not $apiRunning) {
    Write-Host "  [WARN] Stale PID file found (PID: $apiPid), cleaning up" -ForegroundColor Yellow
    Remove-Item $apiPidFile -Force -ErrorAction SilentlyContinue
    $apiRunning = $false
}

Add-Check "API Process" $apiRunning
if ($apiRunning) { Write-Host "  [OK] API running (PID: $apiPid)" -ForegroundColor Green }
else { Write-Host "  [FAIL] API not running" -ForegroundColor Red }

if ($apiRunning) {
    $apiHealthy = Test-HTTP "http://127.0.0.1:8000/api/health"
    Add-Check "API Health Endpoint" $apiHealthy
    if ($apiHealthy) { Write-Host "  [OK] API health endpoint responding" -ForegroundColor Green }
    else { Write-Host "  [FAIL] API health endpoint not responding" -ForegroundColor Red }
    
    # Test specific API endpoints
    # 401 = auth required but endpoint exists (this is correct behavior)
    $devicesApi = Test-HTTP "http://127.0.0.1:8000/api/devices/" 5000 401
    Add-Check "API Devices Endpoint" $devicesApi
    if ($devicesApi) { Write-Host "  [OK] API /devices/ endpoint reachable (auth required)" -ForegroundColor Green }
    else { Write-Host "  [WARN] API /devices/ endpoint issue" -ForegroundColor Yellow }
}

# =====================================
# 4. Dashboard
# =====================================
Write-Host ""
Write-Host "Dashboard:"
$dashboardPidFile = Join-Path $Root "data\runtime\dashboard.pid"
$dashboardPid = $null
$dashboardRunning = $false
try {
    $dashboardPid = Get-ProcessIdFromFile -PidFilePath $dashboardPidFile
} catch {
    Write-ErrorLog "Dashboard PID file issue: $($_.Exception.Message)"
}
if ($dashboardPid) {
    $dashboardRunning = Test-ProcessAlive $dashboardPid
}

# If PID file exists but process is dead, clean it up
if ($dashboardPid -and -not $dashboardRunning) {
    Write-Host "  [WARN] Stale PID file found (PID: $dashboardPid), cleaning up" -ForegroundColor Yellow
    Remove-Item $dashboardPidFile -Force -ErrorAction SilentlyContinue
    $dashboardRunning = $false
}

Add-Check "Dashboard Process" $dashboardRunning
if ($dashboardRunning) { Write-Host "  [OK] Dashboard running (PID: $dashboardPid)" -ForegroundColor Green }
else { Write-Host "  [FAIL] Dashboard not running" -ForegroundColor Red }

if ($dashboardRunning) {
    $dashHttp = Test-DashReady -Hostname "127.0.0.1" -Port 3000
    Add-Check "Dashboard HTTP" $dashHttp
    if ($dashHttp) { Write-Host "  [OK] Dashboard HTTP responding" -ForegroundColor Green }
    else { Write-Host "  [FAIL] Dashboard HTTP not responding" -ForegroundColor Red }
}

# =====================================
# 5. WebSocket
# =====================================
Write-Host ""
Write-Host "WebSocket:"
$wsPort = Test-Port "127.0.0.1" 8000
Add-Check "WebSocket Port" $wsPort
if ($wsPort) { Write-Host "  [OK] WebSocket port 8000 reachable" -ForegroundColor Green }
else { Write-Host "  [FAIL] WebSocket port 8000 not reachable" -ForegroundColor Red }

# =====================================
# 6. LAN Interface
# =====================================
Write-Host ""
Write-Host "LAN Interface ($LanInterface):"
$lanAdapter = Get-NetAdapter -Name $LanInterface -ErrorAction SilentlyContinue
$lanUp = $lanAdapter -and $lanAdapter.Status -eq "Up"
Add-Check "LAN Interface" $lanUp
if ($lanUp) { Write-Host "  [OK] $LanInterface is UP" -ForegroundColor Green }
else { Write-Host "  [FAIL] $LanInterface is DOWN or not found" -ForegroundColor Red }

# =====================================
# 7. LAN IP
# =====================================
Write-Host ""
Write-Host "LAN IP:"
$lanIpObj = Get-NetIPAddress -InterfaceAlias $LanInterface -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1
$lanIp = if ($lanIpObj) { $lanIpObj.IPAddress } else { "" }
$lanIpCorrect = $lanIp -eq $LanIP
Add-Check "LAN IP Address" $lanIpCorrect
if ($lanIpCorrect) { Write-Host "  [OK] LAN IP: $LanIP" -ForegroundColor Green }
else { 
    Write-Host "  [WARN] Expected: $LanIP" -ForegroundColor Yellow
    if ($lanIp) { Write-Host "  Current: $lanIp" }
}

# =====================================
# 8. Gateway
# =====================================
Write-Host ""
Write-Host "Gateway ($GatewayIP):"
$gatewayReachable = Test-Connection -ComputerName $GatewayIP -Count 1 -Quiet -ErrorAction SilentlyContinue
Add-Check "Gateway Reachability" $gatewayReachable "FAIL"
if ($gatewayReachable) { Write-Host "  [OK] Gateway reachable" -ForegroundColor Green }
else { Write-Host "  [FAIL] Gateway unreachable" -ForegroundColor Red }

# =====================================
# 9. Internet Connectivity
# =====================================
Write-Host ""
Write-Host "Internet Connectivity:"
$internetOk = $false
$firstHost = $true
foreach ($testHost in $InternetTestHosts) {
    $test = Test-Connection -ComputerName $testHost -Count 1 -Quiet -ErrorAction SilentlyContinue
    if ($test) {
        $internetOk = $true
        break
    }
    if ($firstHost) { Write-Host "  Testing $testHost..."; $firstHost = $false }
}
Add-Check "Internet Connectivity" $internetOk
if ($internetOk) { Write-Host "  [OK] Internet reachable" -ForegroundColor Green }
else { Write-Host "  [FAIL] No internet connectivity" -ForegroundColor Red }

# =====================================
# 10. DNS Resolution
# =====================================
Write-Host ""
Write-Host "DNS Resolution:"
$dnsOk = $false
foreach ($dns in $DnsServers) {
    try {
        $result = Resolve-DnsName -Name "google.com" -Server $dns -ErrorAction Stop -DnsOnly
        if ($result) { $dnsOk = $true; break }
    } catch { }
}
Add-Check "DNS Resolution" $dnsOk "WARN"
if ($dnsOk) { Write-Host "  [OK] DNS working" -ForegroundColor Green }
else { Write-Host "  [WARN] DNS resolution issues" -ForegroundColor Yellow }

# =====================================
# 11. Packet Capture Capability
# =====================================
Write-Host ""
Write-Host "Packet Capture:"
$pcapOk = $false
try {
    # Check if Npcap/WinPcap is available
    $npcap = Get-Item "C:\Windows\System32\Npcap" -ErrorAction SilentlyContinue
    $winpcap = Get-Item "C:\Windows\System32\wpcap.dll" -ErrorAction SilentlyContinue
    if ($npcap -or $winpcap) { $pcapOk = $true }
} catch { }
Add-Check "Packet Capture Driver" $pcapOk "WARN"
if ($pcapOk) { Write-Host "  [OK] Packet capture driver found" -ForegroundColor Green }
else { Write-Host "  [WARN] Packet capture driver not found" -ForegroundColor Yellow }

# =====================================
# Summary
# =====================================
Write-Host ""
Write-Host "========================================"
Write-Host "SUMMARY"
Write-Host "========================================"

$passed = ($script:Checks | Where-Object { $_.Passed }).Count
$failed = ($script:Checks | Where-Object { -not $_.Passed -and $_.Level -eq "FAIL" }).Count
$warnings = ($script:Checks | Where-Object { -not $_.Passed -and $_.Level -eq "WARN" }).Count

Write-Host "Passed: $passed"
Write-Host "Failed: $failed"
Write-Host "Warnings: $warnings"
Write-Host ""

foreach ($check in $script:Checks) {
    $color = if ($check.Passed) { "Green" } elseif ($check.Level -eq "WARN") { "Yellow" } else { "Red" }
    $status = if ($check.Passed) { "PASS" } else { $check.Level }
    Write-Host "  [$status] $($check.Name)" -ForegroundColor $color
    if ($check.Detail) { Write-Host "    $($check.Detail)" }
}

Write-Host ""
Write-Host "========================================"
if ($script:Healthy) {
    Write-Host "  OVERALL: HEALTHY" -ForegroundColor Green
} else {
    Write-Host "  OVERALL: UNHEALTHY" -ForegroundColor Red
}
Write-Host "========================================"
Write-Host ""

if ($script:Healthy) { exit 0 } else { exit 1 }
