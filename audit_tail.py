import io, os

path = os.path.join("logs", "engine.error.log")
size = os.path.getsize(path)
print("FILE SIZE:", size)

# read last 40KB
with io.open(path, "r", encoding="utf-8", errors="replace") as f:
    f.seek(max(0, size - 40000))
    tail = f.read()

for line in tail.splitlines()[-60:]:
    print(line)

print("\n--- SEARCH dev_003 / 75 / other macs in whole log ---")
hits = 0
with io.open(path, "r", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        if any(k in line for k in ("dev_003", "192.168.137.75", "192.168.137.0", "ERROR", "Traceback", "CRITICAL", "Exception")):
            print(f"L{i}: {line.strip()[:200]}")
            hits += 1
            if hits > 100:
                break
print("total search hits shown:", hits)