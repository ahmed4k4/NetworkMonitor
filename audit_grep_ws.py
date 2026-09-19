import os

terms = ["traffic_update", "device_online", "device_offline", "system_status",
         "broadcast", "emit", "websocket", "websocket"]

for root, dirs, files in os.walk("network-engine"):
    if ".venv" in root:
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            low = line.lower()
            if any(t in low for t in terms):
                if "import" in low and ("scapy" in low or "packaging" in low):
                    continue
                print(f"{path}:{i}: {line.strip()[:160]}")