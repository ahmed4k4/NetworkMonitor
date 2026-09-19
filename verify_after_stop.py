import socket
import psutil

def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False

print("port 3000 open:", port_open(3000))
print("port 8000 open:", port_open(8000))

import os
for pf in ["data/runtime/engine.pid", "data/runtime/api.pid", "data/runtime/dashboard.pid"]:
    print(pf, "exists:", os.path.exists(pf))

print("python procs:")
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        name = p.info["name"] or ""
        cmd = p.info["cmdline"] or []
        if isinstance(name, str) and name.lower().startswith("python"):
            joined = " ".join(cmd)
            if "NetworkMonitor" in joined or ("main.py" in joined) or ("uvicorn" in joined):
                print(f"  PID={p.info['pid']} CMD={joined}")
    except Exception:
        pass