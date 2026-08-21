#!/usr/bin/env python
"""Test device fields"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r = requests.get(API + '/api/devices/', headers=h, timeout=5)
devices = r.json()
for d in devices[:3]:
    print(f'{d["device_id"]}: upload={d.get("upload")} download={d.get("download")} total_today={d.get("total_today")} keys={list(d.keys())}')