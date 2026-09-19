import urllib.request
import json

BASE = "http://127.0.0.1:8000"

def get_token():
    data = json.dumps({"username": "admin", "password": "admin"}).encode()
    req = urllib.request.Request(BASE + "/api/auth/login", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())["access_token"]

TOKEN = get_token()
HDRS = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}

routes = [
    ("GET", "/api/health", None),
    ("GET", "/api/devices", None),
    ("GET", "/api/traffic/summary", None),
    ("GET", "/api/traffic/current", None),
    ("GET", "/api/flows", None),
    ("GET", "/api/dns/domains", None),
    ("GET", "/api/dns/queries", None),
    ("GET", "/api/applications", None),
    ("GET", "/api/analytics/categories", None),
    ("GET", "/api/analytics/protocols", None),
    ("GET", "/api/analytics/activity", None),
    ("GET", "/api/analytics/peaks", None),
    ("GET", "/api/system/status", None),
    ("GET", "/api/system/info", None),
    ("GET", "/api/alerts", None),
    ("GET", "/api/control/rules", None),
    ("GET", "/api/control/limits", None),
]

for method, path, body in routes:
    url = BASE + path
    req = urllib.request.Request(url, method=method, headers=HDRS)
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        # summarize
        if isinstance(parsed, list):
            summary = f"list[{len(parsed)}]"
        elif isinstance(parsed, dict):
            keys = list(parsed.keys())[:6]
            summary = f"dict{keys}"
        else:
            summary = str(parsed)[:60]
        print(f"{method} {path} -> {resp.status} {summary}")
    except urllib.error.HTTPError as e:
        print(f"{method} {path} -> HTTP {e.code}")
    except Exception as e:
        print(f"{method} {path} -> ERR {type(e).__name__}: {e}")