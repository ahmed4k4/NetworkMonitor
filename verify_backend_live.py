"""Live endpoint verification using the ACTUAL route table (from verify_routes_dump.py)."""
import sys, io, json, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "http://127.0.0.1:8000"

def login():
    req = urllib.request.Request(
        BASE + "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        tok = json.load(urllib.request.urlopen(req))["access_token"]
        return {"Authorization": "Bearer " + tok}
    except Exception as e:
        print("LOGIN FAILED:", e)
        sys.exit(1)

H = login()

def call(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=H, method=method)
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, None
    except Exception as e:
        return 0, str(e)

results = []

def probe(name, path, method="GET", body=None):
    status, data = call(method, path, body)
    ok = status in (200, 201)
    detail = ""
    count = None
    if not ok:
        detail = f"HTTP {status} {str(data)[:120]}"
    else:
        if isinstance(data, dict):
            detail = "keys=" + ",".join(list(data.keys())[:5])
            for k, v in data.items():
                if isinstance(v, list):
                    count = len(v)
                    detail += f" | {k}_count={count}"
                    break
        elif isinstance(data, list):
            count = len(data)
            detail = f"count={count}"
    results.append((name, "PASS" if ok else "FAIL", detail))
    return status, data, count

print("Checking API availability...")
probe("health", "/api/health")
probe("system/status", "/api/system/status")
probe("system/interfaces", "/api/system/interfaces")

# Devices + sub-routes
st, devs, n = probe("devices", "/api/devices/")
_device_id = None
if st == 200:
    lst = []
    if isinstance(devs, list):
        lst = devs
    elif isinstance(devs, dict):
        lst = devs.get("devices") or devs.get("items") or []
    if lst:
        _device_id = lst[0].get("device_id") or lst[0].get("id")
if _device_id:
    d = f"/api/devices/{_device_id}"
    probe("device/detail", d)
    probe("device/activity", d + "/activity")
    probe("device/applications", d + "/applications")
    probe("device/categories", d + "/categories")
    probe("device/domains", d + "/domains")
    probe("device/intelligence", d + "/intelligence")
    probe("device/peaks", d + "/peaks")
    probe("device/protocols", d + "/protocols")
    probe("device/sni", d + "/sni")
    probe("device/top-applications", d + "/top-applications")
else:
    results.append(("device/sub-routes", "FAIL", "no device_id found"))

# Traffic
probe("traffic/history", "/api/traffic/history")
probe("traffic/recent", "/api/traffic/recent")

# Analytics
probe("analytics/applications", "/api/analytics/applications")
probe("analytics/daily", "/api/analytics/daily")
probe("analytics/domains", "/api/analytics/domains")
probe("analytics/hourly", "/api/analytics/hourly")
probe("analytics/monthly", "/api/analytics/monthly")
probe("analytics/protocols", "/api/analytics/protocols")
probe("analytics/top-devices", "/api/analytics/top-devices")
probe("analytics/weekly", "/api/analytics/weekly")

# Alerts / flows / applications / dns
probe("alerts", "/api/alerts/")
probe("flows/active", "/api/flows/active")
probe("applications", "/api/applications/")
probe("dns/recent", "/api/dns/recent")

# Reports
probe("reports", "/api/reports/")

# Control: rules/limits/quotas/firewall GET
probe("control/rules", "/api/control/rules")
probe("control/limits", "/api/control/limits")
probe("control/quotas", "/api/control/quotas")
probe("control/firewall", "/api/control/firewall")

# Data management
probe("data/backups", "/api/data-management/backups")
probe("data/stats", "/api/data-management/stats")
probe("data/tables", "/api/data-management/tables")

print("\n=== LIVE BACKEND VERIFICATION (ACTUAL ROUTES) ===\n")
failed = 0
for name, status, detail in results:
    if status == "FAIL":
        failed += 1
    print(f"{status:5s} {name:28s} {detail}")
print(f"\nTOTAL: {len(results)} checks, {failed} failures")