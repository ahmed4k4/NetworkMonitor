import json
import urllib.request

BASE = 'http://127.0.0.1:8000'
def req(method, path, token=None, body=None):
    url = BASE + path
    headers = {}
    data = None
    if body:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(body).encode()
    if token:
        headers['Authorization'] = 'Bearer ' + token
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read().decode() or 'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or 'null')

# login
s, b = req('POST', '/api/auth/login', body={'username': 'admin', 'password': 'admin'})
token = b.get('access_token')

# Check device dev_004 (has IP, MAC, online state)
s, b = req('GET', '/api/devices/dev_004', token=token)
print('=== dev_004 ===')
for k, v in b.items():
    print('  {}: {}'.format(k, v))

# Check device detail endpoints
endpoints = [
    '/api/devices/dev_004/applications',
    '/api/devices/dev_004/domains',
    '/api/devices/dev_004/protocols',
    '/api/devices/dev_004/activity',
    '/api/devices/dev_004/peaks',
]
for ep in endpoints:
    s, b = req('GET', ep, token=token)
    count = len(b) if isinstance(b, list) else 1
    print('{}: {} - {} items'.format(ep, s, count))