#!/usr/bin/env python
"""Test flows"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r = requests.get(API + '/api/flows/active', headers=h, timeout=5)
flows = r.json()
for f in flows[:10]:
    print(f'flow: src={f["source_ip"]}:{f["source_port"]} dst={f["destination_ip"]}:{f["destination_port"]} proto={f["protocol"]} dir={f.get("direction")} state={f["state"]} bytes={f["bytes"]} ul={f.get("upload")} dl={f.get("download")} dev={f.get("device_id")}')