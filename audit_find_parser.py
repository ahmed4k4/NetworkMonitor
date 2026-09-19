import os

terms = ["source_mac", "destination_mac", "def process_packet", "def parse"]

for root, dirs, files in os.walk("network-engine"):
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
            for term in terms:
                if term in line and ("parse" in path.lower() or "analytics" in path.lower() or "capture" in path.lower() or term in ("source_mac", "destination_mac")):
                    print(f"{path}:{i}: {line.strip()[:160]}")