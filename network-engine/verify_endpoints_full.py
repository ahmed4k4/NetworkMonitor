#!/usr/bin/env python
"""Comprehensive live endpoint verification using the actual OpenAPI route map."""
import requests, sys

API = 'http://localhost:8000'
PASS = []
FAIL = []

def login():
    r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin'}, timeout=10)
    assert r.status_code == 200, f"login {r.status_code} {r.text}"
    return r.json()['access_token']

def check(name, method, path, expect=range(200,300), **kw):
    try:
        r = getattr(requests, method)(API + path, timeout=10, **kw)
        ok = r.status_code in expect
        tag = 'PASS' if ok else 'FAIL'
        detail = ''
        try:
            j = r.json()
            if isinstance(j, list):
                detail = f'[{len(j)} items]'
            elif isinstance(j, dict) and 'detail' in j:
                detail = str(j['detail'])[:90]
            elif isinstance(j, dict):
                detail = f'{{{", ".join(list(j.keys())[:6])}}}'
        except Exception:
            detail = r.text[:90]
        print(f'[{tag}] {method.upper():6} {path} -> {r.status_code} {detail}')
        (PASS if ok else FAIL).append(name)
        return r
    except Exception as e:
        print(f'[FAIL] {method.upper():6} {path} -> EXC {e}')
        FAIL.append(name)
        return None

def main():
    token = login()
    h = {'Authorization': f'Bearer {token}'}
    ct = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    dv = 'dev_002'

    # System / health / auth
    check('health', 'get', '/api/health')
    check('docs', 'get', '/docs')
    check('openapi', 'get', '/openapi.json')

    # Devices core
    check('devices_list', 'get', '/api/devices/', headers=h)
    check('devices_detail', 'get', f'/api/devices/{dv}', headers=h)
    check('devices_by_mac', 'get', '/api/devices/mac/20:e8:82:ac:0b:72', headers=h)
    check('devices_name', 'post', f'/api/devices/{dv}/name', headers=ct, json={'name':'Test-Phone'})

    # Device detail sub-resources (categories/protocols/domains/apps/peaks/activity/intel/sni)
    check('devices_categories', 'get', f'/api/devices/{dv}/categories', headers=h)
    check('devices_protocols', 'get', f'/api/devices/{dv}/protocols', headers=h)
    check('devices_domains', 'get', f'/api/devices/{dv}/domains', headers=h)
    check('devices_applications', 'get', f'/api/devices/{dv}/applications', headers=h)
    check('devices_top_applications', 'get', f'/api/devices/{dv}/top-applications', headers=h)
    check('devices_peaks', 'get', f'/api/devices/{dv}/peaks', headers=h)
    check('devices_activity', 'get', f'/api/devices/{dv}/activity', headers=h)
    check('devices_intelligence', 'get', f'/api/devices/{dv}/intelligence', headers=h)
    check('devices_sni', 'get', f'/api/devices/{dv}/sni', headers=h)

    # Traffic
    check('traffic_recent', 'get', '/api/traffic/recent', headers=h)
    check('traffic_history', 'get', f'/api/traffic/history?device_id={dv}', headers=h)

    # Flows
    check('flows_active', 'get', '/api/flows/active', headers=h)

    # DNS
    check('dns_recent', 'get', '/api/dns/recent', headers=h)

    # Applications
    check('applications_list', 'get', '/api/applications/', headers=h)

    # Analytics (domains/protocols/categories/top-devices/daily/weekly/monthly/hourly)
    check('analytics_domains', 'get', '/api/analytics/domains', headers=h)
    check('analytics_protocols', 'get', '/api/analytics/protocols', headers=h)
    check('analytics_applications', 'get', '/api/analytics/applications', headers=h)
    check('analytics_top_devices', 'get', '/api/analytics/top-devices', headers=h)
    check('analytics_daily', 'get', '/api/analytics/daily', headers=h)
    check('analytics_weekly', 'get', '/api/analytics/weekly', headers=h)
    check('analytics_monthly', 'get', '/api/analytics/monthly', headers=h)
    check('analytics_hourly', 'get', '/api/analytics/hourly', headers=h)

    # Control
    check('control_rules', 'get', '/api/control/rules', headers=h)
    check('control_limits', 'get', '/api/control/limits', headers=h)
    check('control_quotas', 'get', '/api/control/quotas', headers=h)
    check('control_firewall', 'get', '/api/control/firewall', headers=h)

    # Alerts
    check('alerts', 'get', '/api/alerts/', headers=h)

    # Reports
    check('reports', 'get', '/api/reports/', headers=h)

    # System
    check('system_status', 'get', '/api/system/status', headers=h)
    check('system_settings', 'get', '/api/system/settings', headers=h)
    check('system_interfaces', 'get', '/api/system/interfaces', headers=h)

    # Data management
    check('data_management_tables', 'get', '/api/data-management/tables', headers=h)
    check('data_management_stats', 'get', '/api/data-management/stats', headers=h)
    check('data_management_backups', 'get', '/api/data-management/backups', headers=h)

    print('\n' + '=' * 60)
    print(f'PASS: {len(PASS)}  FAIL: {len(FAIL)}')
    if FAIL:
        print('FAILED:', FAIL)
        sys.exit(1)
    print('ALL ENDPOINTS VERIFIED')

if __name__ == '__main__':
    main()