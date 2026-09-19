import subprocess, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ps = r"""Get-CimInstance Win32_Process -Filter "Name like '%python%'" | Select-Object ProcessId, CommandLine | Format-List"""
out = subprocess.run(
    ["powershell", "-NoProfile", "-Command", ps],
    capture_output=True, text=True
).stdout
print(out[:8000])