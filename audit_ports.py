import socket
import urllib.request

for port in (3000, 5432, 8000, 8001, 8080, 5000):
    s = socket.socket()
    s.settimeout(1.0)
    try:
        s.connect(("127.0.0.1", port))
        print(f"port {port}: OPEN")
    except Exception as e:
        print(f"port {port}: closed ({type(e).__name__})")
    finally:
        s.close()

# Try common API health endpoints
for url in (
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/api/health",
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000/api/devices",
    "http://127.0.0.1:8000/devices",
    "http://127.0.0.1:8001/health",
    "http://127.0.0.1:8080/health",
    "http://127.0.0.1:3000/",
):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            body = resp.read(300).decode("utf-8", "replace")
            print(f"{url} -> {resp.status} {body[:200]}")
    except Exception as e:
        print(f"{url} -> {type(e).__name__}: {e}")