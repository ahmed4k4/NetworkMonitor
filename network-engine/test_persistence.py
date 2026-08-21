#!/usr/bin/env python
"""Verify quota/limit persistence and immediate UI reflection"""
import requests
import json

API = 'http://localhost:8000'

# Login
r = requests.post(API + '/api/auth/login',
                  json={"username": "admin", "password": "admin_password_change_me"},
                  timeout=5)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Verify persisted quota/limit
r = requests.get(API + '/api/devices/', headers=headers, timeout=5)
dev = next(d for d in r.json() if d["device_id"] == "dev_002")
print("=== PERSISTENCE VERIFICATION ===")
print(f"quota_bytes: {dev['quota_bytes']}")
print(f"download_limit_bps: {dev['download_limit_bps']}")
print(f"upload_limit_bps: {dev['upload_limit_bps']}")

# Update quota and verify immediate reflection
r3 = requests.post(API + '/api/devices/dev_002/quota', headers=headers,
                   json={"daily_quota_mb": 4096, "enabled": True}, timeout=5)
print(f"Update quota response: {r3.status_code}")

r4 = requests.get(API + '/api/devices/', headers=headers, timeout=5)
dev_new = next(d for d in r4.json() if d["device_id"] == "dev_002")
ok = dev_new["quota_bytes"] == 4294967296 and dev_new["download_limit_bps"] == 41943040
print(f"NEW quota_bytes: {dev_new['quota_bytes']} (expected 4294967296)")
print(f"download_limit_bps: {dev_new['download_limit_bps']}")
print(f"RESULT: {'PASS' if ok else 'FAIL'}")