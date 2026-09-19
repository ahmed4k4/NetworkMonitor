import urllib.request
import json

url = "http://127.0.0.1:8000/api/auth/login"
candidates = ["admin", "admin_change_me", "password", "admin123", "12345678"]

for pw in candidates:
    data = json.dumps({"username": "admin", "password": pw}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read().decode()
        print(f"SUCCESS admin/{pw}: {body}")
        break
    except urllib.error.HTTPError as e:
        print(f"FAIL admin/{pw}: {e.code}")