#!/usr/bin/env python
"""Test traffic API"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r = requests.get(API + '/api/traffic/recent', headers=h, timeout=5)
traffic = r.json()
print(f"Type: {type(traffic)}")
print(f"Count: {len(traffic)}")
for t in traffic[:3]:
    print(f'{t}')