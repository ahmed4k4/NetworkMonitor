#!/usr/bin/env python
"""Test quota update/delete"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Update quota
r = requests.post(API + '/api/devices/dev_002/quota', headers=h, json={'daily_quota_mb': 200, 'enabled': True}, timeout=5)
print(f'Quota update: {r.status_code} {r.json()}')

# Check device
r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
d = r.json()
print(f'Device quota after update: quota_bytes={d.get("quota_bytes")} quota_enabled={d.get("quota_enabled")}')

# Test disabling quota
r = requests.post(API + '/api/devices/dev_002/quota', headers=h, json={'enabled': False}, timeout=5)
print(f'Quota disable: {r.status_code} {r.json()}')

r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
d = r.json()
print(f'Device quota after disable: quota_enabled={d.get("quota_enabled")}')