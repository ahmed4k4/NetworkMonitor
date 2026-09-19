import urllib.request
import json

BASE = "http://127.0.0.1:8000"

def get_token():
    data = json.dumps({"username": "admin", "password": "admin"}).encode()
    req = urllib.request.Request(BASE + "/api/auth/login", data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=5).read())["access_token"]

TOKEN = get_token()
HDRS = {"Authorization": "Bearer " + TOKEN}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HDRS)
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

print("=== TRAFFIC recent (first 15) ===")
rows = get("/api/traffic/recent")
for x in rows[:15]:
    print(f"ip={x.get('ip')} dl={x.get('download')} ul={x.get('upload')} dl_bps={x.get('download_speed_bps')} ul_bps={x.get('upload_speed_bps')} pkts={x.get('packets')} conns={x.get('connections')} t={x.get('time')}")

print("\n=== DEVICES (full first 3) ===")
devs = get("/api/devices/")
for d in devs[:3]:
    print(json.dumps(d, indent=1)[:800])

print("\n=== ANALYTICS applications (first 3, full) ===")
apps = get("/api/analytics/applications")
for a in apps[:3]:
    print(json.dumps(a, indent=1))

print("\n=== ANALYTICS domains (first 3, full) ===")
doms = get("/api/analytics/domains")
for d in doms[:3]:
    print(json.dumps(d, indent=1))

print("\n=== ANALYTICS protocols (full) ===")
for p in get("/api/analytics/protocols"):
    print(json.dumps(p))

print("\n=== ANALYTICS hourly (count) ===")
print("hourly len:", len(get("/api/analytics/hourly")))
print("daily len:", len(get("/api/analytics/daily")))