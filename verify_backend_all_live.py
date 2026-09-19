import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000"


def req(method, path, token=None, body=None, timeout=15):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, method=method, data=data, headers=headers)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        raw = resp.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return resp.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def summarize(parsed):
    if isinstance(parsed, list):
        return f"list[{len(parsed)}]"
    if isinstance(parsed, dict):
        keys = list(parsed.keys())[:8]
        return f"dict{keys}"
    return f"{str(parsed)[:60]}"


results = []

# 1. Health (no auth)
code, data = req("GET", "/api/health")
results.append(("health", code, data))
print(f"GET /api/health -> {code} {summarize(data)}")

# 2. Auth - wrong password should fail
code, data = req("POST", "/api/auth/login", body={"username": "admin", "password": "WRONGPASS"})
results.append(("auth_bad_login", code, data))
print(f"POST /api/auth/login (bad) -> {code} {summarize(data)}")

# 3. Auth - correct login gets token
code, data = req("POST", "/api/auth/login", body={"username": "admin", "password": "admin"})
print(f"POST /api/auth/login (ok) -> {code}")
TOKEN = None
if code == 200 and isinstance(data, dict):
    TOKEN = data.get("access_token") or data.get("token")
    print(f"   token obtained: {'yes' if TOKEN else 'NO'}")
else:
    print(f"   FAILED to login: {summarize(data)}")

if not TOKEN:
    print("AUTH FAILED - cannot continue endpoint verification")
else:
    # 4. Unauthenticated access to devices must be rejected (401/403)
    code, _ = req("GET", "/api/devices")
    print(f"GET /api/devices (no auth) -> {code} (expect 401/403)")

    ENDPOINTS = [
        ("GET", "/api/devices", None, "devices"),
        ("GET", "/api/traffic/summary", None, "traffic_summary"),
        ("GET", "/api/traffic/current", None, "traffic_current"),
        ("GET", "/api/flows", None, "flows"),
        ("GET", "/api/dns/domains", None, "domains"),
        ("GET", "/api/dns/queries", None, "dns_queries"),
        ("GET", "/api/applications", None, "applications"),
        ("GET", "/api/analytics/categories", None, "categories"),
        ("GET", "/api/analytics/protocols", None, "protocols"),
        ("GET", "/api/analytics/activity", None, "activity"),
        ("GET", "/api/analytics/peaks", None, "peaks"),
        ("GET", "/api/system/status", None, "system_status"),
        ("GET", "/api/system/info", None, "system_info"),
        ("GET", "/api/alerts", None, "alerts"),
        ("GET", "/api/control/rules", None, "rules"),
        ("GET", "/api/control/limits", None, "limits"),
        ("GET", "/api/control/quotas", None, "quotas"),
        ("GET", "/api/firewall/rules", None, "firewall"),
        ("GET", "/api/reports", None, "reports"),
        ("GET", "/api/interfaces", None, "interfaces"),
        ("GET", "/api/system/status", None, "system"),
        ("GET", "/api/data", None, "data_management"),
    ]

    for method, path, body, name in ENDPOINTS:
        code, data = req(method, path, TOKEN, body)
        results.append((name, code, data))
        print(f"{method} {path} -> {code} {summarize(data)}")

        # Device detail - use first device id if present
        if name == "devices" and code == 200 and isinstance(data, list) and data:
            did = data[0].get("device_id")
            if did:
                code, dd = req("GET", f"/api/devices/{did}", TOKEN)
                results.append(("device_detail", code, dd))
                print(f"GET /api/devices/{did} -> {code} {summarize(dd)}")

    # Device-specific sub-resources for first device
    code, data = req("GET", "/api/devices", TOKEN)
    if code == 200 and isinstance(data, list) and data:
        did = data[0].get("device_id")
        for sub, name in [
            (f"/api/devices/{did}/traffic", "device_traffic"),
            (f"/api/devices/{did}/history", "device_history"),
            (f"/api/devices/{did}/applications", "device_applications"),
            (f"/api/devices/{did}/domains", "device_domains"),
            (f"/api/devices/{did}/categories", "device_categories"),
            (f"/api/devices/{did}/protocols", "device_protocols"),
            (f"/api/devices/{did}/activity", "device_activity"),
            (f"/api/devices/{did}/peaks", "device_peaks"),
            (f"/api/devices/{did}/flows", "device_flows"),
        ]:
            code, dd = req("GET", sub, TOKEN)
            results.append((name, code, dd))
            print(f"GET {sub} -> {code} {summarize(dd)}")

print("\n=== SUMMARY ===")
fails = []
for name, code, _ in results:
    if code is None or code >= 500:
        fails.append((name, code))
    elif name == "auth_bad_login" and code not in (401, 403):
        fails.append((name, code))
    elif name == "devices" and code == 200 and isinstance(data := req("GET", "/api/devices", TOKEN)[1], list) and False:
        pass

if fails:
    print("FAILURES:")
    for f in fails:
        print("  ", f)
else:
    print("NO FAILURES - all endpoints responded without 5xx/connection errors")