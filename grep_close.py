import os, re

root = 'network-engine'
for dirpath, dirs, files in os.walk(root):
    for fn in files:
        if not fn.endswith('.py'):
            continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f, 1):
                    if '.close()' in line and 'cursor' not in line and 'sock' not in line:
                        print(f"{p}:{i}: {line.strip()}")
        except Exception as e:
            print(f"ERR {p}: {e}")