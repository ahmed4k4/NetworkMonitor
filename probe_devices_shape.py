import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
B = "http://127.0.0.1:8000"
req = urllib.request.Request(B + "/api/auth/login",
    data=json.dumps({"username": "admin", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"})
H = {"Authorization": "Bearer " + json.load(urllib.request.urlopen(req))["access_token"]}
req = urllib.request.Request(B + "/api/devices/", headers=H)
data = json.load(urllib.request.urlopen(req))
print("type:", type(data).__name__)
print(json.dumps(data[:2], indent=2, default=str))