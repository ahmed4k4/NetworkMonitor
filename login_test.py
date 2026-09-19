import json
import urllib.request
import urllib.error
import sys

BASE = "http://127.0.0.1:8000"

def post(endpoint, payload):
    req = urllib.request.Request(
        BASE + endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

# 1. Correct credentials
for creds in [("admin", "admin"), ("admin", "admin_change_me")]:
    status, body = post("/api/auth/login", {"username": creds[0], "password": creds[1]})
    print(f"LOGIN {creds[0]}/{creds[1]} -> {status}: {json.dumps(body)[:200]}")

# 2. Wrong password
status, body = post("/api/auth/login", {"username": "admin", "password": "wrongpass"})
print(f"LOGIN admin/wrongpass -> {status}: {json.dumps(body)[:200]}")

# 3. Valid token on protected endpoint
status, body = post("/api/auth/login", {"username": "admin", "password": "admin"})
if status == 200:
    token = body["access_token"]
    print(f"TOKEN len={len(token)} prefix={token[:25]}...")
    req = urllib.request.Request(
        BASE + "/api/devices",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=10)
        devices = json.loads(r.read().decode())
        print(f"GET /api/devices (Bearer) -> {r.status}, {len(devices)} devices")
        if devices:
            d = devices[0]
            print("   sample device:", json.dumps({k: d.get(k) for k in ('device_id','hostname','ip','mac','state')}))
    except urllib.error.HTTPError as e:
        print(f"GET /api/devices -> {e.code}: {e.read().decode()[:300]}")

# 4. No token on protected endpoint
req = urllib.request.Request(BASE + "/api/devices")
try:
    urllib.request.urlopen(req, timeout=10)
    print("GET /api/devices (no token) -> UNEXPECTED 200")
except urllib.error.HTTPError as e:
    print(f"GET /api/devices (no token) -> {e.code} (expected 401/403)")

# 5. Health (public)
req = urllib.request.Request(BASE + "/api/health")
try:
    r = urllib.request.urlopen(req, timeout=10)
    print(f"GET /api/health -> {r.status}: {r.read().decode()[:200]}")
except urllib.error.HTTPError as e:
    print(f"GET /api/health -> {e.code}")