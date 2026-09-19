"""Live endpoint verification: exercise every API group and report status + real data counts."""
import sys, io, json, urllib.request, os
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
        H = {"Authorization": "Bearer " + tok}
        return H
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

def probe(name, path, method="GET", expect_200=True):
    status, data = call(method, path)
    ok = True
    detail = ""
    if expect_200 and status != 200:
        ok = False
        detail = f"HTTP {status} {str(data)[:120]}"
    else:
        # classify payload
        if isinstance(data, dict):
            detail = "keys=" + ",".join(list(data.keys())[:4])
            # find first list inside for count
            for k, v in data.items():
                if isinstance(v, list):
                    detail += f" | {k}_count={len(v)}"
                    break
        elif isinstance(data, list):
            detail = f"count={len(data)}"
    results.append((name, "PASS" if ok else "FAIL", detail))

# health
probe("health", "/api/health")
# system
probe("system", "/api/system/status")
probe("system/interfaces", "/api/system/interfaces")
# devices
probe("devices", "/api/devices")
# traffic
probe("traffic", "/api/traffic/summary")
probe("traffic/hourly", "/api/traffic/hourly")
probe("traffic/speed", "/api/traffic/speed")
probe("traffic/packets", "/api/traffic/packets")
# applications
probe("applications", "/api/applications")
# domains
probe("domains", "/api/domains")
# categories
probe("categories", "/api/categories")
# protocols
probe("protocols", "/api/protocols")
# activity
probe("activity/peaks", "/api/activity/peaks")
probe("activity/alerts", "/api/activity/alerts")
# flows
probe("flows", "/api/flows?limit=5")
# rules
probe("rules", "/api/rules")
# limits
probe("limits", "/api/limits")
# quotas
probe("quotas", "/api/quotas")
# firewall
probe("firewall", "/api/firewall")
# reports
probe("reports", "/api/reports")
# data management
probe("data_management", "/api/data/management")

# history for a device
st, devs = call("GET", "/api/devices")
if st == 200:
    devs = devs["devices"] if isinstance(devs, dict) else devs
    if devs:
        did = devs[0]["device_id"]
        probe("device_detail", f"/api/devices/{did}")
        probe("device_history", f"/api/devices/{did}/history")

print("\n=== LIVE ENDPOINT VERIFICATION ===\n")
failed = 0
for name, status, detail in results:
    mark = "PASS" if status == "PASS" else "FAIL"
    if status == "FAIL":
        failed += 1
    print(f"{mark:5s} {name:24s} {detail}")
print(f"\nTOTAL: {len(results)} checks, {failed} failures")