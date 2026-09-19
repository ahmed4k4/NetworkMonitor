import os

terms = ["process_packet", "save_flow", "device_id", "Error saving flow"]

for root, dirs, files in os.walk("network-engine"):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
        except Exception:
            continue
        for term in terms:
            if term in txt:
                # print line numbers
                lines = txt.splitlines()
                for i, line in enumerate(lines, 1):
                    if term in line:
                        print(f"{path}:{i}: {line.strip()[:160]}")