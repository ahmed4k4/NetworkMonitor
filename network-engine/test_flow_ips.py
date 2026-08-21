#!/usr/bin/env python
"""Test flow IPs"""
import requests

API = 'http://localhost:8000'
r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

r = requests.get(API + '/api/flows/active', headers=h, timeout=5)
flows = r.json()
for f in flows[:3]:
    print(f'source_ip: "{f["source_ip"]}" dest_ip: "{f["destination_ip"]}"')