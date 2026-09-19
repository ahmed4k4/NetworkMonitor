import json, urllib.request

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJBRE1JTiIsImV4cCI6MTc4ODMwMTYxNCwidHlwZSI6ImFjY2VzcyJ9.K9eqFC4Hr43u6Iun8tJwBjp3gSEBVzU4z6nC2ul6N9w"
BASE = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

print("=== /api/devices/dev_002 ===")
d = get("/api/devices/dev_002")
for k in ["device_id","ip","ip_address","mac","mac_address","hostname","state","status",
          "download_today","upload_today","total_today","download_speed_bps","upload_speed_bps",
          "current_speed_bps","download_bytes","upload_bytes","last_seen","first_seen"]:
    if k in d:
        print(f"  {k}: {d[k]}")
print("  ALL KEYS:", sorted(d.keys()))

print()
print("=== /api/devices (list) ===")
dl = get("/api/devices")
for row in dl:
    print(f"  {row.get('device_id')} | ip={row.get('ip') or row.get('ip_address')} | mac={row.get('mac') or row.get('mac_address')} | state={row.get('state')} | down_today={row.get('download_today')} up_today={row.get('upload_today')}")

print()
print("=== /api/devices/dev_002/intelligence?range=24h ===")
try:
    intel = get("/api/devices/dev_002/intelligence?range=24h")
    print(json.dumps(intel, indent=2, default=str)[:2000])
except Exception as e:
    print("ERROR:", e)

print()
print("=== /api/devices/dev_002/applications?range=24h ===")
try:
    print(json.dumps(get("/api/devices/dev_002/applications?range=24h"), indent=2, default=str)[:1500])
except Exception as e:
    print("ERROR:", e)

print()
print("=== /api/devices/dev_002/domains?range=24h ===")
try:
    print(json.dumps(get("/api/devices/dev_002/domains?range=24h"), indent=2, default=str)[:1500])
except Exception as e:
    print("ERROR:", e)