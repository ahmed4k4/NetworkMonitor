#!/usr/bin/env python
"""Test quota API"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Test quota API
r = requests.post(API + '/api/devices/dev_002/quota', headers=h, json={'daily_quota_mb': 100, 'enabled': True}, timeout=5)
print(f'Quota set: {r.status_code} {r.json()}')

# Check device
r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
d = r.json()
print(f'Device quota: quota_bytes={d.get("quota_bytes")} quota_enabled={d.get("quota_enabled")} usage_pct={d.get("usage_percentage")}')