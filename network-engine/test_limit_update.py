#!/usr/bin/env python
"""Test limit update/disable"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Update limit
r = requests.post(API + '/api/devices/dev_002/limit?ip=192.168.137.2', headers=h, json={'download_limit': 2048, 'upload_limit': 1024, 'enabled': True}, timeout=5)
print(f'Limit update: {r.status_code} {r.json()}')

# Check device
r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
d = r.json()
print(f'Device limit after update: download_limit_bps={d.get("download_limit_bps")} upload_limit_bps={d.get("upload_limit_bps")} limit_enabled={d.get("limit_enabled")}')

# Test disabling limit
r = requests.post(API + '/api/devices/dev_002/limit?ip=192.168.137.2', headers=h, json={'enabled': False}, timeout=5)
print(f'Limit disable: {r.status_code} {r.json()}')

r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
d = r.json()
print(f'Device limit after disable: limit_enabled={d.get("limit_enabled")}')