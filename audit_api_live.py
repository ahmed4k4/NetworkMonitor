"""Live API contract audit against the running server."""
import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8000"

def call(method, path, token=None, body=None, params=None):
    url = BASE + path
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url += ("&" if "?" in url else "?") + qs
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw[:300]
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:300]
    except Exception as e:
        return "ERR", repr(e)


# 1. login
st, login = call("POST", "/api/auth/login", body={"username": "admin", "password": "admin"})
print("LOGIN", st)
if st != 200:
    print("  ->", login); raise SystemExit(1)
token = login.get("access_token") or login.get("token")
print("  keys:", list(login.keys()))
print("  token len:", len(token or ""))

for path, params in [
    ("/api/health", None),
    ("/api/devices", None),
    ("/api/devices/", None),
    ("/api/analytics/domains", None),
    ("/api/analytics/applications", None),
    ("/api/analytics/protocols", None),
    ("/api/analytics/top-devices", None),
    ("/api/analytics/hourly", None),
    ("/api/analytics/daily", None),
    ("/api/flows", {"limit": 3}),
    ("/api/dns/queries", {"limit": 3}),
    ("/api/traffic/samples", {"limit": 3}),
    ("/api/traffic/current", None),
    ("/api/system/interfaces", None),
    ("/api/alerts", None),
    ("/api/data-management/stats", None),
]:
    st, data = call("GET", path, token=token, params=params)
    if isinstance(data, dict):
        keys = list(data.keys())
        extra = ""
        if "devices" in data: extra = f" devices={len(data['devices'])}"
        if "domains" in data: extra = f" domains={len(data['domains'])}"
        if "items" in data: extra = f" items={len(data['items'])}"
        if "top_devices" in data: extra = f" top_devices={len(data['top_devices'])}"
    else:
        keys, extra = "?", ""
    print(f"GET {path} -> {st}{extra} keys={keys}")

# unauth check (should be 401)
st, data = call("GET", "/api/devices")
print("UNAUTH /api/devices ->", st, "(expect 401)")

# current-speed endpoints
for path in ["/api/traffic/current-speeds", "/api/analytics/current"]:
    st, data = call("GET", path, token=token)
    print(f"GET {path} -> {st}")