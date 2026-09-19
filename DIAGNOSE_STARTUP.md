# Diagnose START.ps1 Failures

## Reported failures
1. Network Engine: process (PID 60748) exited before health check passed → RESULT=FAILED
2. Dashboard: executable not found 'npm.cmd' → RESULT=FAILED

## Plan
- STEP 1: Inspect START.ps1, HEALTH.ps1, STATUS.ps1, scripts/common.ps1, engine entry, dashboard config
- STEP 2: Verify Python env (.venv) + critical imports
- STEP 3: Run engine manually, capture real stderr/stdout
- STEP 4: Verify Windows network interfaces (Get-NetAdapter, Get-NetIPConfiguration)
- STEP 5: Test Npcap/packet capture directly
- STEP 6: Run dashboard manually (npm/node resolution)
- STEP 7: Diagnose START.ps1 root causes
- STEP 8: Fix only real causes (launcher robustness)
- STEP 9: Do NOT touch app data logic
- STEP 10: Real verification (manual start, ports, logs, START.ps1, HEALTH.ps1)