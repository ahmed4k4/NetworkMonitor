$targets = @(
    'network-engine\database\repository.py',
    'network-engine\database\aggregation.py',
    'network-engine\database\audit.py',
    'network-engine\api\auth.py',
    'network-engine\api\routes\control.py',
    'network-engine\api\routes\devices.py',
    'network-engine\api\routes\analytics.py',
    'network-engine\control\quotas.py',
    'network-engine\engine.py',
    'network-engine\discovery\identity.py',
    'network-engine\discovery\scanner.py',
    'network-engine\flow\'
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        $m = Select-String -Path $t -Pattern '\.close\(\)'
        foreach ($x in $m) {
            Write-Output ($x.Path + ':' + $x.LineNumber + ': ' + $x.Line.Trim())
        }
    }
}
Write-Output '--- recursive flow/discovery/capture/events ---'
$dirs = @('network-engine\flow','network-engine\discovery','network-engine\capture','network-engine\events')
foreach ($d in $dirs) {
    if (Test-Path $d) {
        $files = Get-ChildItem -Path $d -Filter '*.py' -Recurse
        foreach ($f in $files) {
            $m = Select-String -Path $f.FullName -Pattern '\.close\(\)'
            foreach ($x in $m) {
                Write-Output ($x.Path + ':' + $x.LineNumber + ': ' + $x.Line.Trim())
            }
        }
    }
}