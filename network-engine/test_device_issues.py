#!/usr/bin/env python
"""Test device issues"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r = requests.get(API + '/api/devices/', headers=h, timeout=5)
devices = r.json()
for d in devices:
    print(f'{d["device_id"]}: ip={d["ip"]} mac={d["mac"]} state={d["state"]} vendor={d["vendor"]} total_up={d.get("total_upload")} total_dl={d.get("total_download")} today_up={d.get("upload_today")} today_dl={d.get("download_today")}')