import os

terms = [
    "Math.random", "random", "dummy", "mock", "fake", "demo",
    "sample", "fallback", "hardcoded", "placeholder", "seed",
    "Math.floor", "Math.round", "Math.ceil",
]

for root, dirs, files in os.walk("dashboard"):
    if ".next" in root or "node_modules" in root or "test-results" in root:
        continue
    for fn in files:
        if not fn.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        path = os.path.join(root, fn)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            low = line.lower()
            for term in terms:
                if term.lower() in low:
                    print(f"{path}:{i}: {line.strip()[:140]}")
                    break