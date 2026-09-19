import os

path = "dashboard/app/devices/page.tsx"
with open(path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()

keywords = ["filter", "ip", "hostname", "displayName", "name", "slice", "sort", "state"]
for i, line in enumerate(lines, 1):
    low = line.lower()
    if any(k in low for k in keywords):
        print(f"{i}: {line.strip()[:160]}")