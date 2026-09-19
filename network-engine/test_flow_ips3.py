#!/usr/bin/env python
"""Test flow IPs types"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r = requests.get(API + '/api/flows/active', headers=h, timeout=5)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
flows = r.json()
for f in flows[:3]:
    print(f'source_ip type={type(f["source_ip"])} value="{f["source_ip"]}"')