import json
import urllib.request
import urllib.error

API = "http://127.0.0.1:8000"


def http(method, path, body=None, token=None):
    url = API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode() or "null")
        except Exception:
            detail = None
        return e.code, detail
    except Exception as e:
        return 0, {"error": str(e)}


# 1. Login
status, login = http("POST", "/api/auth/login", {"username": "admin", "password": "admin"})
print("LOGIN", status, json.dumps(login)[:300])
token = login.get("access_token") if isinstance(login, dict) else None

if not token:
    # try common password
    for pw in ["admin123", "password", "Admin@123", "admin@123", "network"]:
        status, login = http("POST", "/api/auth/login", {"username": "admin", "password": pw})
        if isinstance(login, dict) and login.get("access_token"):
            token = login["access_token"]
            print("LOGIN OK with password", pw)
            break
        print("LOGIN TRY", pw, status, str(login)[:120])

if not token:
    raise SystemExit("NO TOKEN")

# 2. List devices
status, devices = http("GET", "/api/devices/", token=token)
print("\nDEVICES", status, "count=", len(devices) if isinstance(devices, list) else devices)
if isinstance(devices, list) and devices:
    d = devices[0]
    id_key = next((k for k in ("id", "device_id") if k in d), None)
    dev_id = d.get(id_key) or d.get("device_id")
    print("FIRST DEVICE keys:", sorted(d.keys()))
    print("FIRST DEVICE sample:", json.dumps(d, indent=2)[:1500])

    # 3. Hit every intelligence endpoint for this device
    endpoints = [
        f"/api/devices/{dev_id}",
        f"/api/devices/{dev_id}/intelligence?range=24h",
        f"/api/devices/{dev_id}/applications?range=24h",
        f"/api/devices/{dev_id}/domains?range=24h&limit=50",
        f"/api/devices/{dev_id}/categories?range=24h",
        f"/api/devices/{dev_id}/protocols?range=24h",
        f"/api/devices/{dev_id}/activity?days=7",
        f"/api/devices/{dev_id}/peaks?days=30",
        f"/api/traffic/recent?device_id={dev_id}",
        f"/api/traffic/history?device_id={dev_id}&days=7",
        f"/api/flows/active?device_id={dev_id}",
    ]
    for ep in endpoints:
        s, body = http("GET", ep, token=token)
        if isinstance(body, list):
            desc = f"list[{len(body)}]"
            sample = json.dumps(body[0], indent=2)[:400] if body else "[]"
        elif isinstance(body, dict):
            desc = "dict " + ",".join(sorted(body.keys())[:12])
            sample = json.dumps(body, indent=2)[:400]
        else:
            desc = str(body)[:100]
            sample = str(body)[:200]
        print(f"\n=== {ep} -> {s} ({desc})")
        print(sample)