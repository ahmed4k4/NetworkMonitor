#!/usr/bin/env python
"""Test devices API returns real usage"""
import requests

API = 'http://localhost:8000'

# Login
r = requests.post(API + '/api/auth/login',
                  json={"username": "admin", "password": "admin_change_me"},
                  timeout=5)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check all devices
r = requests.get(API + '/api/devices/', headers=headers, timeout=5)
devices = r.json()
print("All devices with usage data:")
for dev in devices:
    if dev.get('total_today', 0) > 0 or dev.get('download_today', 0) > 0 or dev.get('upload_today', 0) > 0:
        print(f"  {dev['device_id']} ({dev.get('ip')}): total_today={dev.get('total_today')} download_today={dev.get('download_today')} upload_today={dev.get('upload_today')} speed_dl={dev.get('download_speed_bps')} speed_ul={dev.get('upload_speed_bps')}")