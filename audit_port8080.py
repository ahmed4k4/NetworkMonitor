import urllib.request
import urllib.error

def probe(url):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=4) as resp:
            body = resp.read(500).decode("utf-8", "replace")
            print(f"{url}\n  -> {resp.status} {dict(resp.headers)}\n  {body[:300]}\n")
    except urllib.error.HTTPError as e:
        body = e.read(500).decode("utf-8", "replace")
        print(f"{url}\n  -> HTTP {e.code} {dict(e.headers)}\n  {body[:300]}\n")
    except Exception as e:
        print(f"{url}\n  -> {type(e).__name__}: {e}\n")

for u in (
    "http://127.0.0.1:8080/",
    "http://127.0.0.1:8080/docs",
    "http://127.0.0.1:8080/openapi.json",
    "http://127.0.0.1:8080/api/health",
    "http://127.0.0.1:8080/api/devices",
    "http://127.0.0.1:8080/health",
):
    probe(u)