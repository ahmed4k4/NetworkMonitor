# Quick smoke test for ConvertFrom-SimpleYaml
. "$PSScriptRoot\common.ps1"

$c = ConvertFrom-SimpleYaml -Text (Get-Content "$PSScriptRoot\..\config\system.yaml" -Raw)

$checks = @(
    @{ Label = "lan_ip";       Value = $c.network.lan_ip;        Expect = "192.168.137.1" },
    @{ Label = "gateway";      Value = $c.network.upstream_gateway; Expect = "192.168.137.2" },
    @{ Label = "lan_interface";Value = $c.network.lan_interface;  Expect = "Ethernet" },
    @{ Label = "db_host";      Value = $c.database.host;          Expect = "127.0.0.1" },
    @{ Label = "db_port";      Value = $c.database.port;          Expect = 5432 },
    @{ Label = "api_port";     Value = $c.api.port;               Expect = 8000 },
    @{ Label = "dash_port";    Value = $c.dashboard.port;         Expect = 3000 },
    @{ Label = "backup_path";  Value = $c.backup.pg_dump_path;    Expect = "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" }
)

$failed = 0
foreach ($ck in $checks) {
    $actual = $ck.Value
    if ($actual -eq $ck.Expect) {
        Write-Host ("PASS {0} = {1}" -f $ck.Label, $actual) -ForegroundColor Green
    } else {
        Write-Host ("FAIL {0} = '{1}' (expected '{2}')" -f $ck.Label, $actual, $ck.Expect) -ForegroundColor Red
        $failed++
    }
}

# Arrays
$dns = @($c.dns_servers)
if ($dns.Count -eq 2 -and $dns[0] -eq "8.8.8.8" -and $dns[1] -eq "1.1.1.1") {
    Write-Host "PASS dns_servers = 8.8.8.8,1.1.1.1" -ForegroundColor Green
} else {
    Write-Host ("FAIL dns_servers = '{0}'" -f ($dns -join ',')) -ForegroundColor Red
    $failed++
}

$hosts = @($c.internet_test_hosts)
if ($hosts.Count -eq 3) {
    Write-Host ("PASS internet_test_hosts = {0}" -f ($hosts -join ',')) -ForegroundColor Green
} else {
    Write-Host ("FAIL internet_test_hosts = '{0}'" -f ($hosts -join ',')) -ForegroundColor Red
    $failed++
}

$scanInterval = $c.network.scan_interval
if ($scanInterval -eq 10) {
    Write-Host "PASS scan_interval = 10" -ForegroundColor Green
} else {
    Write-Host ("FAIL scan_interval = '{0}'" -f $scanInterval) -ForegroundColor Red
    $failed++
}

if ($failed -eq 0) {
    Write-Host "ALL PARSER TESTS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host ("{0} parser tests FAILED" -f $failed) -ForegroundColor Red
    exit 1
}