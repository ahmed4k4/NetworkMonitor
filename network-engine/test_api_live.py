import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
import time
import requests

# Wait for API to come up
for _ in range(30):
    try:
        requests.get("http://127.0.0.1:8000/", timeout=1)
        break
    except Exception:
        time.sleep(1)

from api.auth import create_access_token
token = create_access_token('admin', 'ADMIN')
headers = {"Authorization": f"Bearer {token}"}

print("=== /api/analytics/domains ===")
r = requests.get("http://127.0.0.1:8000/api/analytics/domains", headers=headers, timeout=10)
print("status:", r.status_code)
data = r.json()
print("count:", len(data))
for row in data[:8]:
    print(" ", row)

print("\n=== /api/analytics/applications ===")
r = requests.get("http://127.0.0.1:8000/api/analytics/applications", headers=headers, timeout=10)
print("status:", r.status_code)
data = r.json()
print("count:", len(data))
for row in data[:8]:
    print(" ", row)

print("\n=== /api/devices/dev_001/intelligence ===")
r = requests.get("http://127.0.0.1:8000/api/devices/dev_001/intelligence?range=24h", headers=headers, timeout=10)
print("status:", r.status_code)
try:
    data = r.json()
    if isinstance(data, dict):
        print("keys:", list(data.keys()))
        print("top_domains:", data.get("top_domains", [])[:5])
        print("top_applications:", data.get("top_applications", [])[:5])
    else:
        print("response:", data)
except Exception as e:
    print("err:", e, r.text[:500])