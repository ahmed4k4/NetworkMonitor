#!/usr/bin/env python
"""Test traffic samples are being saved"""
import requests
import time

API = 'http://localhost:8000'

# Login
r = requests.post(API + '/api/auth/login',
                  json={"username": "admin", "password": "admin_password_change_me"},
                  timeout=5)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Wait for engine sampling cycle (50 seconds)
print("Waiting for engine sample cycle...")
time.sleep(55)

# Check traffic samples
r = requests.get(API + '/api/traffic/recent', headers=headers, timeout=5)
traffic = r.json()
print(f"Traffic samples: {len(traffic)}")
for t in traffic[:5]:
    print(f"  device={t['device_id']} dl={t['download']} ul={t['upload']} dl_spd={t.get('download_speed_bps')} ul_spd={t.get('upload_speed_bps')}")

# Check devices for usage
r = requests.get(API + '/api/devices/', headers=headers, timeout=5)
devices = r.json()
for dev in devices:
    if dev.get('total_today', 0) > 0 or dev.get('download_today', 0) > 0 or dev.get('upload_today', 0) > 0:
        print(f"Device with usage: {dev['device_id']} total={dev.get('total_today')} dl={dev.get('download_today')} ul={dev.get('upload_today')}")