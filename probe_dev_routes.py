import json, urllib.request as u, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
B = "http://127.0.0.1:8000/api/"
def g(p, t):
    r = u.Request(B + p, headers={"Authorization": "Bearer " + t})
    try:
        with u.urlopen(r, timeout=8) as e:
            return e.status, json.loads(e.read().decode())
    except Exception as e:
        return None, str(e)
login = json.loads(u.urlopen(u.Request(B + "auth/login", data=json.dumps({"username": "admin", "password": "admin"}).encode(), headers={"Content-Type": "application/json"}), timeout=8).read())
t = login["access_token"]; print("token", bool(t))
for ep in ["devices/dev_002", "devices/dev_002/traffic?limit=3", "devices/dev_002/flows?limit=3",
           "devices/dev_002/history", "devices/dev_002/activity", "devices/dev_002/applications",
           "devices/dev_002/domains", "devices/dev_002/categories", "devices/dev_002/protocols",
           "devices/dev_002/peaks"]:
    s, d = g(ep, t)
    print("===", ep, s)
    print(json.dumps(d, default=str)[:350] if s == 200 else str(d)[:150])