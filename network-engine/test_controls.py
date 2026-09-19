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

device_id = 'dev_004'

# Test rename - using POST /api/devices/{device_id}/name
print('=== Testing Rename ===')
s, b = req('POST', '/api/devices/{}/name'.format(device_id), token=token, body={'name': 'Test Device'})
print('Rename: {} - {}'.format(s, b))

# Verify rename
s, b = req('GET', '/api/devices/{}'.format(device_id), token=token)
print('After rename: custom_name = {}'.format(b.get('custom_name')))

# Test block
print('\n=== Testing Block ===')
s, b = req('POST', '/api/devices/{}/block'.format(device_id), token=token)
print('Block: {} - {}'.format(s, b))

# Verify block
s, b = req('GET', '/api/devices/{}'.format(device_id), token=token)
print('After block: state = {}'.format(b.get('state')))

# Test unblock
print('\n=== Testing Unblock ===')
s, b = req('POST', '/api/devices/{}/unblock'.format(device_id), token=token)
print('Unblock: {} - {}'.format(s, b))

# Verify unblock
s, b = req('GET', '/api/devices/{}'.format(device_id), token=token)
print('After unblock: state = {}'.format(b.get('state')))

# Test speed limit
print('\n=== Testing Speed Limit ===')
s, b = req('POST', '/api/devices/{}/limit'.format(device_id), token=token, body={'download_limit_bps': 5000000, 'upload_limit_bps': 2000000})
print('Set limit: {} - {}'.format(s, b))

# Test data limit (quota)
print('\n=== Testing Quota ===')
s, b = req('POST', '/api/devices/{}/quota'.format(device_id), token=token, body={'quota_bytes': 209715200})  # 200MB
print('Set quota: {} - {}'.format(s, b))

# Test rules CRUD
print('\n=== Testing Rules CRUD ===')
s, b = req('GET', '/api/control/rules', token=token)
print('List rules: {} - {} rules'.format(s, len(b)))

s, b = req('POST', '/api/control/rules', token=token, body={'name': 'Test Rule', 'action': 'BLOCK', 'device_mac': '0c:2f:b0:5a:a0:6a'})
print('Create rule: {} - {}'.format(s, b))
rule_id = b.get('id') if s == 200 else None

if rule_id:
    s, b = req('GET', '/api/control/rules/{}'.format(rule_id), token=token)
    print('Get rule: {} - {}'.format(s, b.get('name')))

    s, b = req('PUT', '/api/control/rules/{}'.format(rule_id), token=token, body={'name': 'Updated Rule', 'action': 'THROTTLE', 'device_mac': '0c:2f:b0:5a:a0:6a'})
    print('Update rule: {} - {}'.format(s, b))

    s, b = req('DELETE', '/api/control/rules/{}'.format(rule_id), token=token)
    print('Delete rule: {} - {}'.format(s, b))

# Test limits CRUD
print('\n=== Testing Limits CRUD ===')
s, b = req('GET', '/api/control/limits', token=token)
print('List limits: {} - {} limits'.format(s, len(b)))

# Test quotas CRUD
print('\n=== Testing Quotas CRUD ===')
s, b = req('GET', '/api/control/quotas', token=token)
print('List quotas: {} - {} quotas'.format(s, len(b)))

# Test firewall CRUD
print('\n=== Testing Firewall CRUD ===')
s, b = req('GET', '/api/control/firewall', token=token)
print('List firewall rules: {} - {} rules'.format(s, len(b)))