#!/usr/bin/env python
"""Verify control actions persist to the database (block/limit/quota/rules CRUD)."""
import requests, sys, json

API = 'http://127.0.0.1:8000'
PASS = []
FAIL = []

def login():
    r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin'}, timeout=10)
    assert r.status_code == 200, f"login {r.status_code} {r.text}"
    return r.json()['access_token']

def report(name, ok, detail=''):
    tag = 'PASS' if ok else 'FAIL'
    print(f'[{tag}] {name} {detail}')
    (PASS if ok else FAIL).append(name)

def main():
    token = login()
    h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    dv = 'dev_002'

    # Device must have an IP for block/limit
    d = requests.get(f'{API}/api/devices/{dv}', headers=h, timeout=10).json()
    ip = d.get('ip')
    report('device_has_ip', bool(ip), f'ip={ip}')

    # --- RENAME (persistence) ---
    r = requests.post(f'{API}/api/devices/{dv}/name', headers=h, json={'name':'Audit-Test-Phone'}, timeout=10)
    report('rename_action', r.status_code == 200, f'{r.status_code}')
    d2 = requests.get(f'{API}/api/devices/{dv}', headers=h, timeout=10).json()
    report('rename_persisted', d2.get('custom_name') == 'Audit-Test-Phone', f"custom_name={d2.get('custom_name')}")

    # --- BLOCK (persistence) ---
    r = requests.post(f'{API}/api/devices/{dv}/block', headers=h, timeout=10)
    report('block_action', r.status_code in (200,201,400), f'{r.status_code} {r.text[:80]}')
    fw = requests.get(f'{API}/api/control/firewall', headers=h, timeout=10).json()
    blocked = [x for x in fw if x.get('device_id') == dv or (x.get('ip') and ip and x.get('ip') == ip)]
    report('block_persisted', len(blocked) > 0, f'firewall rules matching={len(fw)} blocked_matches={len(blocked)}')

    # --- UNBLOCK ---
    r = requests.post(f'{API}/api/devices/{dv}/unblock', headers=h, timeout=10)
    report('unblock_action', r.status_code in (200,201,400), f'{r.status_code} {r.text[:80]}')

    # --- SPEED LIMIT (persistence) ---
    r = requests.post(f'{API}/api/devices/{dv}/limit', headers=h,
        json={'download_limit': 500, 'upload_limit': 250, 'enabled': True}, timeout=10)
    report('limit_action', r.status_code == 200, f'{r.status_code} {r.text[:80]}')
    lims = requests.get(f'{API}/api/control/limits', headers=h, timeout=10).json()
    match = [x for x in lims if x.get('device_id') == dv]
    report('limit_persisted', len(match) > 0, f'limits={len(lims)} match={len(match)}')

    # --- DATA LIMIT / QUOTA (persistence) ---
    r = requests.post(f'{API}/api/devices/{dv}/quota', headers=h,
        json={'daily_quota_mb': 1024, 'action': 'ALERT', 'enabled': True}, timeout=10)
    report('quota_action', r.status_code == 200, f'{r.status_code} {r.text[:80]}')
    quotas = requests.get(f'{API}/api/control/quotas', headers=h, timeout=10).json()
    match = [x for x in quotas if x.get('device_id') == dv]
    report('quota_persisted', len(match) > 0, f'quotas={len(quotas)} match={len(match)}')

    # --- RULES CRUD ---
    # Create
    r = requests.post(f'{API}/api/control/rules', headers=h,
        json={'name':'Audit Test Rule','action':'BLOCK','condition':{'type':'domain','value':'example.com'},'enabled':True}, timeout=10)
    rule_created = r.status_code in (200,201)
    report('rule_create', rule_created, f'{r.status_code} {r.text[:120]}')
    rule_id = None
    if r.status_code in (200,201):
        try:
            j = r.json()
            rule_id = j.get('id') or j.get('rule_id')
        except Exception:
            rule_id = None

    rules = requests.get(f'{API}/api/control/rules', headers=h, timeout=10).json()
    rule_match = [x for x in rules if str(x.get('name') or '').startswith('Audit Test Rule')]
    report('rule_persisted', len(rule_match) > 0, f'rules={len(rules)} match={len(rule_match)}')

    # Find actual id from GET if POST didn't return one
    if rule_id is None and rule_match:
        rule_id = rule_match[0].get('id') or rule_match[0].get('rule_id')

    # Edit (enable/disable)
    if rule_id is not None:
        r = requests.put(f'{API}/api/control/rules/{rule_id}', headers=h,
            json={'enabled': False}, timeout=10)
        report('rule_edit', r.status_code == 200, f'{r.status_code} {r.text[:100]}')

        # Delete
        r = requests.delete(f'{API}/api/control/rules/{rule_id}', headers=h, timeout=10)
        report('rule_delete', r.status_code in (200,204), f'{r.status_code} {r.text[:80]}')

        rules2 = requests.get(f'{API}/api/control/rules', headers=h, timeout=10).json()
        still_there = [x for x in rules2 if (x.get('id') == rule_id or x.get('rule_id') == rule_id)]
        report('rule_delete_persisted', len(still_there) == 0, f'remaining={len(still_there)}')
    else:
        report('rule_edit', False, 'no rule id returned')
        report('rule_delete', False, 'no rule id returned')
        report('rule_delete_persisted', False, 'no rule id returned')

    print('\n' + '=' * 60)
    print(f'PASS: {len(PASS)}  FAIL: {len(FAIL)}')
    if FAIL:
        print('FAILED:', FAIL)
        sys.exit(1)
    print('ALL CONTROL PERSISTENCE CHECKS PASSED')

if __name__ == '__main__':
    main()