#!/usr/bin/env python
"""Test speed limit API with IP"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Test speed limit API - requires IP parameter
r = requests.post(API + '/api/devices/dev_002/limit?ip=192.168.137.2', headers=h, json={'download_limit': 1024, 'upload_limit': 512, 'enabled': True}, timeout=5)
print(f'Limit set: {r.status_code} {r.json()}')

# Check device
r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
d = r.json()
print(f'Device limit: download_limit_bps={d.get("download_limit_bps")} upload_limit_bps={d.get("upload_limit_bps")} limit_enabled={d.get("limit_enabled")} limit_id={d.get("limit_id")}')