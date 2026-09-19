import subprocess, json, urllib.request, urllib.error
# List python processes
out = subprocess.run(["powershell","-NoProfile","-Command",
  "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Select-Object ProcessId,CommandLine | Out-String"],
  capture_output=True, text=True)
print("=== PYTHON PROCESSES ===")
print(out.stdout)
print("=== API /system/status ===")
BASE="http://127.0.0.1:8000"
def call(method, path, token=None, body=None):
    url=BASE+path
    req=urllib.request.Request(url, method=method)
    if token: req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type","application/json")
        data=json.dumps(body).encode()
    else:
        data=None
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return "ERR", repr(e)
st, login = call("POST","/api/auth/login", body={"username":"admin","password":"admin"})
tok = json.loads(login)["access_token"]
for path in ["/api/system/status","/api/system/interfaces","/api/control/status"]:
    s, b = call("GET", path, tok)
    print(f"{s} {path}")
    try:
        print(json.dumps(json.loads(b), indent=2)[:1500])
    except Exception:
        print(b[:300])