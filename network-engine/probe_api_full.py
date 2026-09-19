import urllib.request
import json

BASE = "http://127.0.0.1:8000"

def get_token():
    data = json.dumps({"username": "admin", "password": "admin"}).encode()
    req = urllib.request.Request(BASE + "/api/auth/login", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())["access_token"]

TOKEN = get_token()
HDRS = {"Authorization": "Bearer " + TOKEN}

def call(method, path):
    req = urllib.request.Request(BASE + path, method=method, headers=HDRS)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode()
        try:
            return resp.status, json.loads(raw)
        except Exception:
            return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {e}"

# Serve non-GET routes without side effects as GET (will 405, that's fine to list)
routes = [
    ("GET", "/api/devices/"),
    ("GET", "/api/traffic/recent"),
    ("GET", "/api/traffic/history"),
    ("GET", "/api/flows/active"),
    ("GET", "/api/dns/recent"),
    ("GET", "/api/applications/"),
    ("GET", "/api/analytics/applications"),
    ("GET", "/api/analytics/domains"),
    ("GET", "/api/analytics/protocols"),
    ("GET", "/api/analytics/hourly"),
    ("GET", "/api/analytics/daily"),
    ("GET", "/api/analytics/weekly"),
    ("GET", "/api/analytics/monthly"),
    ("GET", "/api/analytics/top-devices"),
    ("GET", "/api/system/status"),
    ("GET", "/api/system/interfaces"),
    ("GET", "/api/system/settings"),
    ("GET", "/api/alerts/"),
    ("GET", "/api/control/rules"),
    ("GET", "/api/control/limits"),
    ("GET", "/api/control/quotas"),
    ("GET", "/api/control/firewall"),
    ("GET", "/api/data-management/tables"),
    ("GET", "/api/data-management/stats"),
    ("GET", "/api/reports/"),
]

for method, path in routes:
    status, body = call(method, path)
    if isinstance(body, list):
        summary = f"list[{len(body)}]"
        if body:
            summary += " first_keys=" + str(list(body[0].keys()))[:120] if isinstance(body[0], dict) else ""
    elif isinstance(body, dict):
        summary = "dict keys=" + str(list(body.keys()))[:120]
    else:
        summary = str(body)[:80]
    print(f"{method} {path} -> {status} {summary}")