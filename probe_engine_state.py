import sys, io, json, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
B = "http://127.0.0.1:8000"

def req(m, p, b=None, t=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(B + p, data=d, method=m)
    r.add_header("Content-Type", "application/json")
    if t: r.add_header("Authorization", "Bearer %s" % t)
    try:
        with urllib.request.urlopen(r, timeout=15) as e:
            return e.status, json.loads(e.read().decode())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode())
        except: return e.code, {}
    except Exception as e:
        return 0, str(e)

st, r = req("POST", "/api/auth/login", {"username": "admin", "password": "admin"})
t = r.get("access_token") or r.get("token")
print("login:", st, bool(t))
if not t:
    sys.exit(1)

for ep in ["/api/system/status", "/api/system/engine", "/api/interfaces/", "/api/system/traffic"]:
    st, d = req("GET", ep, t=t)
    print("=== %s (%s) ===" % (ep, st))
    print(json.dumps(d, indent=2, default=str)[:2500])
    print()
