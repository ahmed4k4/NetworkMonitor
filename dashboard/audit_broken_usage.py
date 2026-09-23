import os, re

root = "dashboard"
patterns = {
    "getDeviceTraffic": r"getDeviceTraffic\b",
    "getDeviceTrafficHistory": r"getDeviceTrafficHistory\b",
    "getFlows": r"\bgetFlows\b",
    "getDeviceFlows": r"getDeviceFlows\b",
    "getDNS": r"\bgetDNS\b",
    "getDomains": r"\bgetDomains\b",
    "getTraffic": r"\bgetTraffic\b",
    "getInterfaces": r"getInterfaces\b",
    "getSettings": r"getSettings\b",
    "getDevice": r"\bgetDevice\b",
    "getDeviceIntelligence": r"getDeviceIntelligence\b",
    "getDeviceApplications": r"getDeviceApplications\b",
    "getDeviceActivity": r"getDeviceActivity\b",
    "getDevicePeaks": r"getDevicePeaks\b",
}

for dirpath, _, files in os.walk(root):
    if "node_modules" in dirpath or ".next" in dirpath:
        continue
    for f in files:
        if not f.endswith((".ts", ".tsx")):
            continue
        fp = os.path.join(dirpath, f)
        src = open(fp, encoding="utf-8", errors="replace").read()
        for name, pat in patterns.items():
            for m in re.finditer(pat, src):
                print(f"{os.path.relpath(fp, root)}: uses {name} (line {src[:m.start()].count(chr(10))+1})")
                break