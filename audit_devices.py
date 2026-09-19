"""Inspect real API response shapes for key endpoints (devices + one device detail)."""
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
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return "ERR", repr(e)

st, login = call("POST", "/api/auth/login", body={"username": "admin", "password": "admin"})
print("login", st)
token = login["access_token"]

st, devs = call("GET", "/api/devices/", token)
print("devices status", st, "count", len(devs) if isinstance(devs, list) else devs)
if isinstance(devs, list):
    d0 = devs[0]
    print("device[0] keys:", sorted(d0.keys()))
    print("device[0] sample:", json.dumps(d0, default=str)[:800])
    # find a device with traffic
    with open("e:/NetworkMonitor/audit_dev.json", "w") as f:
        json.dump(devs, f, default=str)

# device detail for each id
for dev in devs[:3]:
    did = dev.get("device_id") or dev.get("id")
    st, dd = call("GET", f"/api/devices/{did}", token)
    print(f"\n--- detail {did} status {st}")
    if isinstance(dd, dict):
        print("detail keys:", sorted(dd.keys()))
        print(json.dumps(dd, default=str)[:1200])
        for sub in ["applications", "domains", "categories", "protocols", "activity", "peaks", "sni"]:
            st2, d2 = call("GET", f"/api/devices/{did}/{sub}", token, {"range":"24h"})
            kind = type(d2).__name__ if not isinstance(d2,(dict,list)) else (f"list[{len(d2)}]" if isinstance(d2,list) else "dict[]"+",".join(sorted(d2.keys())[:8]))
            print(f"   /{sub} -> {st2} {kind}")
            if isinstance(d2, list) and d2:
                print("      sample:", json.dumps(d2[0], default=str)[:500])