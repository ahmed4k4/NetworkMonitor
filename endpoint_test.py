import json, urllib.request, urllib.error
BASE = "http://127.0.0.1:8000"

def post(endpoint, payload):
    req = urllib.request.Request(BASE+endpoint, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=10); return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

# login
st, body = post("/api/auth/login", {"username":"admin","password":"admin"})
token = body["access_token"]
H = {"Authorization": f"Bearer {token}"}

def get(endpoint, timeout=15):
    req = urllib.request.Request(BASE+endpoint, headers=H)
    try:
        r = urllib.request.urlopen(req, timeout=timeout); return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

endpoints = [
    "/api/devices",
    "/api/analytics/applications",
    "/api/analytics/domains",
    "/api/analytics/protocols",
    "/api/analytics/categories",
    "/api/analytics/top-devices",
    "/api/analytics/hourly",
    "/api/analytics/daily",
    "/api/applications",
    "/api/domains",
]
for ep in endpoints:
    try:
        st2, data = get(ep)
        if isinstance(data, list):
            print(f"GET {ep} -> {st2}  list[{len(data)}] sample={json.dumps(data[0])[:200] if data else '-'}")
        elif isinstance(data, dict):
            print(f"GET {ep} -> {st2}  keys={list(data.keys())[:12]}  len(top?) = {len(data.get('top_applications',[])) if 'top_applications' in data else '-'}")
        else:
            print(f"GET {ep} -> {st2}  {json.dumps(data)[:200]}")
    except Exception as e:
        print(f"GET {ep} -> EXC {type(e).__name__} {e}")

# device detail + intelligence
st, devs = get("/api/devices")
if devs:
    did = devs[0]["device_id"]
    print(f"\nUsing device {did}")
    for ep in [f"/api/devices/{did}", f"/api/devices/{did}/intelligence?range=24h",
               f"/api/devices/{did}/applications?range=24h", f"/api/devices/{did}/domains?range=24h",
               f"/api/devices/{did}/connections"]:
        try:
            st2, data = get(ep, timeout=20)
            if isinstance(data, dict):
                keys = list(data.keys())
                listkeys = {k: len(data[k]) for k in data if isinstance(data[k], list)}
                print(f"GET {ep} -> {st2}  keys={keys[:14]}  lists={listkeys}")
            elif isinstance(data, list):
                print(f"GET {ep} -> {st2}  list[{len(data)}]")
            else:
                print(f"GET {ep} -> {st2}")
        except Exception as e:
            print(f"GET {ep} -> EXC {type(e).__name__} {e}")