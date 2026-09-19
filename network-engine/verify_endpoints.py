import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

def req(method, path, token=None, body=None, timeout=10):
    url = BASE + path
    headers = {}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "null")
        except Exception:
            return e.code, None
    except Exception as e:
        return -1, str(e)

# login
status, body = req("POST", "/api/auth/login", body={"username": "admin", "password": "admin"})
token = body.get("access_token") if status == 200 else None
print("LOGIN:", status, "token=", bool(token))

# Get OpenAPI schema
status, schema = req("GET", "/openapi.json")
print("OPENAPI:", status)
paths = sorted(schema.get("paths", {}).keys())
print("TOTAL PATHS:", len(paths))
for p in paths:
    print("  ", p)

# Test each path (GET-safe only; for POST/PUT/DELETE report method, skip mutations)
print("\n=== ENDPOINT STATUS ===")
results = []
for p in paths:
    ops = schema["paths"][p]
    for method in ops:
        if method in ("get", "post", "put", "delete", "patch"):
            # Fill path params with placeholder
            test_path = p
            # Use empty/dev_004 placeholders for {device_id}
            test_path = test_path.replace("{device_id}", "dev_004")
            test_path = test_path.replace("{flow_id}", "1")
            test_path = test_path.replace("{id}", "1")
            s, b = req(method.upper(), test_path, token=token)
            results.append((method.upper(), test_path, s))
            print(f"  {method.upper():6s} {test_path:50s} -> {s}")

# Summary
fails = [r for r in results if r[2] >= 500]
auth_fails = [r for r in results if r[2] == 401]
print("\n=== SUMMARY ===")
print("Total", len(results), "| 5xx:", len(fails), "| 401:", len(auth_fails))