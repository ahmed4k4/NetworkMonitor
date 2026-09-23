import urllib.request
import json

def get(url, h=None):
    r = urllib.request.Request(url, headers=h or {})
    return urllib.request.urlopen(r, timeout=5)

req = urllib.request.Request("http://localhost:8000/api/auth/login",
    data=json.dumps({"username": "admin", "password": "admin_change_me"}).encode(),
    headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=5)
tok = json.loads(resp.read()).get("access_token") or json.load(open).get("token")
h = {"Authorization": "Bearer " + tok} if tok else {}
d = get("http://localhost:8000/api/v1/devices", h)
print("devices", d.status, d.read(900).decode("utf-8", "replace"))

paths = ["/api/v1/devices", "/devices", "/api/devices", "/health"]
for port in (8000, 8080):
    for path in paths:
        try:
            r = urllib.request.urlopen("http://localhost:%d%s" % (port, path), timeout=3)
            print(port, path, r.status, r.read(200).decode("utf-8", "replace")[:150])
        except Exception as e:
            print(port, path, type(e).__name__)