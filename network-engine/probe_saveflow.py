import re
p = r"network-engine/database/repository.py"
src = open(p, encoding="utf-8", errors="replace").read()
lines = src.splitlines()
for i, ln in enumerate(lines, 1):
    if "save_flow" in ln or "INSERT INTO flows" in ln or "class Flow" in ln:
        start = max(0, i - 3)
        end = min(len(lines), i + 12)
        print(f"===== around line {i} =====")
        for j in range(start, end):
            print(f"{j+1}: {lines[j]}")