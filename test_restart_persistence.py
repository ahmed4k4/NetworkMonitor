import psycopg
import requests
import json
import time

print("=" * 80)
print("RESTART PERSISTENCE TEST")
print("=" * 80)

base_url = "http://127.0.0.1:8000"

def get_token():
    login_resp = requests.post(f"{base_url}/api/auth/login", json={"username": "admin", "password": "admin_change_me"})
    return login_resp.json().get("access_token")

def test_api_endpoints(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test key endpoints
    endpoints = [
        "/api/analytics/daily?device_id=dev_003",
        "/api/analytics/hourly?device_id=dev_003",
        "/api/analytics/weekly?device_id=dev_003",
        "/api/analytics/monthly?device_id=dev_003",
        "/api/devices/dev_003",
    ]
    
    results = {}
    for ep in endpoints:
        resp = requests.get(f"{base_url}{ep}", headers=headers)
        if resp.status_code == 200:
            results[ep] = resp.json()
        else:
            results[ep] = f"ERROR {resp.status_code}"
    return results

# Get baseline data
print("\n1. BASELINE DATA (before restart)")
print("-" * 40)
token = get_token()
baseline = test_api_endpoints(token)

# Show key values
print("Daily for dev_003:")
for d in baseline.get("/api/analytics/daily?device_id=dev_003", []):
    print(f"  {d['time']}: DL={d['download']}, UL={d['upload']}")

print("\nDevice detail dev_003:")
dev = baseline.get("/api/devices/dev_003", {})
if isinstance(dev, dict):
    print(f"  download_today: {dev.get('download_today')}")
    print(f"  upload_today: {dev.get('upload_today')}")
    print(f"  total_download: {dev.get('download')}")
    print(f"  total_upload: {dev.get('upload')}")

# Now restart the API server
print("\n2. RESTARTING API SERVER...")
print("-" * 40)
import subprocess
import sys

# Kill existing uvicorn
subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
time.sleep(3)

# Start new API server
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000"], 
                        cwd=r"e:\NetworkMonitor\network-engine")
time.sleep(5)

print("\n3. DATA AFTER API RESTART")
print("-" * 40)
try:
    token = get_token()
    after_api = test_api_endpoints(token)
    
    print("Daily for dev_003:")
    for d in after_api.get("/api/analytics/daily?device_id=dev_003", []):
        print(f"  {d['time']}: DL={d['download']}, UL={d['upload']}")
    
    print("\nDevice detail dev_003:")
    dev = after_api.get("/api/devices/dev_003", {})
    if isinstance(dev, dict):
        print(f"  download_today: {dev.get('download_today')}")
        print(f"  upload_today: {dev.get('upload_today')}")
        print(f"  total_download: {dev.get('download')}")
        print(f"  total_upload: {dev.get('upload')}")
    
    # Compare
    print("\n4. COMPARISON")
    print("-" * 40)
    if baseline == after_api:
        print("  ✓ ALL DATA IDENTICAL AFTER API RESTART")
    else:
        print("  ✗ DATA DIFFERS!")
        for k in baseline:
            if baseline[k] != after_api.get(k):
                print(f"    DIFF in {k}")
                print(f"      Before: {json.dumps(baseline[k], default=str)[:200]}")
                print(f"      After:  {json.dumps(after_api.get(k), default=str)[:200]}")
except Exception as e:
    print(f"  Error: {e}")

# Test database directly
print("\n5. DIRECT DATABASE CHECK (after API restart)")
print("-" * 40)
conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute("""
        SELECT day_start::text, download_bytes, upload_bytes
        FROM usage_daily
        WHERE device_id = 'dev_003'
        ORDER BY day_start DESC;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: DL={row[1]}, UL={row[2]}")
conn.close()

proc.terminate()
print("\n" + "=" * 80)
print("RESTART TEST COMPLETE")
print("=" * 80)