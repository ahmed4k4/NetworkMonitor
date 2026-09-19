import os

for root, dirs, files in os.walk("network-engine"):
    for fn in files:
        if not fn.endswith(".py") or ".venv" in root:
            continue
        path = os.path.join(root, fn)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            low = line.lower()
            if any(t in low for t in ["ip_address", "upsert_device", "arp", "discover", "def scan", "mark_online", "update_device_status"]):
                if "def " in line or "ip_address" in line or "arp" in low or "discover" in low:
                    print(f"{path}:{i}: {line.strip()[:160]}")