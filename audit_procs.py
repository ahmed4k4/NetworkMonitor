import psutil

for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        info = p.info
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
    name = (info.get("name") or "").lower()
    cmd = " ".join(info.get("cmdline") or [])
    if any(k in cmd.lower() for k in ("uvicorn", "api.app", "engine", "main.py", "next", "node", "run_api", "networkmonitor")):
        print(f"PID {info.get('pid')} | {name} | {cmd[:200]}")