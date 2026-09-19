import json, urllib.request, urllib.error
BASE = "http://127.0.0.1:8000"
def call(method, path, token=None, params=None, body=None):
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k,v in params.items())
    req = urllib.request.Request(url, method=method)
    if token: req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return "ERR", repr(e)

st, login = call("POST", "/api/auth/login", body={"username":"admin","password":"admin"})
token = login["access_token"]

for p in ["/api/data-management/stats","/api/data-management/api/data-management/stats",
          "/api/data-management/tables","/api/data-management/api/data-management/tables",
          "/api/data-management/backups"]:
    st, data = call("GET", p, token)
    if isinstance(data, dict):
        keys = list(data.keys())[:12]
        extra = f" keys={keys}"
    else:
        extra = f" type={type(data).__name__}"
    print(f"{st} {p}{extra}")

# control endpoints that frontend uses
for p in ["/api/control/limits","/api/control/quotas","/api/control/firewall","/api/control/rules",
          "/api/system/status","/api/system/settings","/api/reports","/api/alerts/","/api/traffic/recent",
          "/api/traffic/history","/api/flows/active","/api/dns/recent","/api/applications/"]:
    st, data = call("GET", p + ("" if "?" in p else ""), token, params={"limit":2} if "traffic/history" in p else None)
    info = ""
    if isinstance(data, list): info = f" list[{len(data)}]"
    elif isinstance(data, dict): info = " dict " + ",".join(list(data.keys())[:6])
    print(f"{st} {p}{info}")