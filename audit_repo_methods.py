import os

path = "network-engine/database/repository.py"
with open(path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()

terms = ["def ", "speed_limits", "data_limits", "network_rules", "firewall_rules", "usage_history"]
for i, line in enumerate(lines, 1):
    low = line.lower()
    if any(t.lower() in low for t in terms):
        print(f"{i}: {line.strip()[:140]}")