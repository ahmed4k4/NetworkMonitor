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
        headers['Authorization'] = f'Bearer {token}'
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read().decode() or 'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or 'null')

# login
s, b = req('POST', '/api/auth/login', body={'username': 'admin', 'password': 'admin'})
token = b.get('access_token')

# test /api/devices/
s, b = req('GET', '/api/devices/', token=token)
print('DEVICES:', s, len(b))
for d in b:
    print('  {}: ip={}, mac={}, state={}, name={}'.format(
        d['device_id'], d['ip'], d['mac'], d['state'], d.get('custom_name') or d.get('hostname')
    ))

# test /api/devices/dev_009 (the one with null ip)
s, b = req('GET', '/api/devices/dev_009', token=token)
print('DEV_009:', s, b.get('ip'), b.get('mac'))