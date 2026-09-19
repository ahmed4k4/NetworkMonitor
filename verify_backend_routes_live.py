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
        keys = list(parsed.keys())[:6]
        return f"dict{keys}"
    return f"{str(parsed)[:50]}"


# Login
code, data = req("POST", "/api/auth/login", body={"username": "admin", "password": "admin"})
print(f"POST /api/auth/login -> {code}")
TOKEN = (data or {}).get("access_token") or (data or {}).get("token")
print(f"   token: {'yes' if TOKEN else 'NO'}")
if not TOKEN:
    raise SystemExit("AUTH FAILED")

# Unauthenticated rejection
code, _ = req("GET", "/api/devices/")
print(f"GET /api/devices/ (no auth) -> {code} (expect 401/403)")

GET_ENDPOINTS = [
    "/api/health",
    "/api/devices/",
    "/api/traffic/recent",
    "/api/traffic/history",
    "/api/flows/active",
    "/api/dns/recent",
    "/api/applications/",
    "/api/analytics/top-devices",
    "/api/analytics/hourly",
    "/api/analytics/daily",
    "/api/analytics/weekly",
    "/api/analytics/monthly",
    "/api/analytics/protocols",
    "/api/analytics/domains",
    "/api/analytics/applications",
    "/api/control/rules",
    "/api/control/limits",
    "/api/control/firewall",
    "/api/control/quotas",
    "/api/data-management/stats",
    "/api/data-management/tables",
    "/api/data-management/backups",
    "/api/system/status",
    "/api/system/interfaces",
    "/api/system/settings",
    "/api/alerts/",
    "/api/reports/",
]

# Devices list for detail/sub-resources
code, devs = req("GET", "/api/devices/", TOKEN)
print(f"GET /api/devices/ -> {code} list[{len(devs) if isinstance(devs, list) else '?'}]")
did = devs[0]["device_id"] if isinstance(devs, list) and devs else None
print(f"   first device_id: {did}")

if did:
    GET_ENDPOINTS += [
        f"/api/devices/{did}",
        f"/api/devices/{did}/intelligence",
        f"/api/devices/{did}/applications",
        f"/api/devices/{did}/domains",
        f"/api/devices/{did}/categories",
        f"/api/devices/{did}/top-applications",
        f"/api/devices/{did}/protocols",
        f"/api/devices/{did}/peaks",
        f"/api/devices/{did}/activity",
        f"/api/devices/{did}/sni",
    ]

fails = []
for path in GET_ENDPOINTS:
    code, data = req("GET", path, TOKEN)
    tag = "OK " if code == 200 else ("ERR" if code is None or code >= 500 else f"{code}")
    print(f"GET {path} -> {code} {summarize(data)}")
    if code == 200:
        pass
    elif code in (401, 403):
        print(f"   WARNING: requires extra scope? {summarize(data)}")
    else:
        fails.append((path, code))

print("\n=== GET RESULT ===")
print("FAILURES:", fails if fails else "NONE - all live GET endpoints responded")