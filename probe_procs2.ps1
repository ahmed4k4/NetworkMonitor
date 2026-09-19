Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*.exe" } | ForEach-Object {
    "PID=$($_.ProcessId) | EXE=$($_.ExecutablePath) | CMD=$($_.CommandLine)"
}
"--- PID FILES ---"
Get-ChildItem "data\runtime\*.pid" -ErrorAction SilentlyContinue | ForEach-Object {
    "$($_.Name): $( (Get-Content $_.FullName -Raw).Trim() )"
}