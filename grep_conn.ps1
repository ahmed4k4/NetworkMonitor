$files = Get-ChildItem -Path 'network-engine' -Filter '*.py' -Recurse | Where-Object { $_.FullName -notmatch '\\\.venv\\|\\__pycache__\\' }
foreach ($f in $files) {
    $matches = Select-String -Path $f.FullName -Pattern 'get_connection|return_connection'
    foreach ($m in $matches) {
        Write-Output ($f.FullName + ':' + $m.LineNumber + ': ' + $m.Line.Trim())
    }
}