import os, re

# 1. Extract registered routes from backend route files
routes = []
routes_dir = "network-engine/api/routes"
for fn in os.listdir(routes_dir):
    if not fn.endswith(".py"):
        continue
    fp = os.path.join(routes_dir, fn)
    src = open(fp, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"@router\.(get|post|put|delete)\s*\(\s*[\"']([^\"']+)[\"']", src):
        method, path = m.group(1), m.group(2)
        routes.append((fn, method.upper(), path))

print("=== REGISTERED BACKEND ROUTES ===")
for fn, method, path in sorted(routes):
    print(f"{method:6s} {path:50s} ({fn})")

# 2. Extract API client endpoint calls
print("\n=== API CLIENT CALLS ===")
client_src = open("dashboard/lib/api.ts", encoding="utf-8", errors="replace").read()
for m in re.finditer(r"request<[^>]*>\(\s*[\"'](/[^\"']*)[\"']", client_src):
    print(f"  {m.group(1)}")