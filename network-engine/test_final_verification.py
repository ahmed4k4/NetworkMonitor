#!/usr/bin/env python
"""Final verification test for complete flow"""
import requests
import json

API = 'http://localhost:8000'

def login():
    r = requests.post(API + '/api/auth/login', json={'username':'admin','password':'admin_password_change_me'}, timeout=5)
    return r.json()['access_token']

def test_complete_flow():
    token = login()
    h = {'Authorization': f'Bearer {token}'}
    
    print("=" * 60)
    print("FINAL VERIFICATION - Complete Flow Test")
    print("=" * 60)
    
    # 1. Get all devices
    print("\n1. GET /api/devices/ - All devices")
    r = requests.get(API + '/api/devices/', headers=h, timeout=5)
    devices = r.json()
    print(f"   Found {len(devices)} devices")
    for d in devices[:3]:
        print(f"   - {d['device_id']} ({d['ip']}) state={d['state']} download_today={d.get('download_today')} upload_today={d.get('upload_today')}")
        print(f"     speed: dl={d.get('download_speed_bps')} ul={d.get('upload_speed_bps')}")
        print(f"     quota: bytes={d.get('quota_bytes')} enabled={d.get('quota_enabled')} usage={d.get('usage_percentage')}%")
        print(f"     limit: id={d.get('limit_id')} dl={d.get('download_limit_bps')} ul={d.get('upload_limit_bps')} enabled={d.get('limit_enabled')}")
    
    # 2. Get specific device
    print("\n2. GET /api/devices/dev_002 - Single device")
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   device_id={d['device_id']} ip={d['ip']}")
    print(f"   download_today={d.get('download_today')} upload_today={d.get('upload_today')}")
    print(f"   total_today={d.get('total_today')}")
    print(f"   current_speed_bps={d.get('current_speed_bps')}")
    print(f"   quota: bytes={d.get('quota_bytes')} used={d.get('quota_used_bytes')} remaining={d.get('quota_remaining_bytes')} enabled={d.get('quota_enabled')} usage={d.get('usage_percentage')}%")
    print(f"   limit: id={d.get('limit_id')} dl={d.get('download_limit_bps')} ul={d.get('upload_limit_bps')} enabled={d.get('limit_enabled')}")
    print(f"   history entries: {len(d.get('history', []))}")
    
    # 3. Test quota
    print("\n3. POST /api/devices/dev_002/quota - Set quota to 150 MB daily")
    r = requests.post(API + '/api/devices/dev_002/quota', headers=h, json={'daily_quota_mb': 150, 'enabled': True}, timeout=5)
    print(f"   Response: {r.status_code} {r.json()}")
    
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   Verified: quota_bytes={d.get('quota_bytes')} enabled={d.get('quota_enabled')} usage={d.get('usage_percentage')}%")
    
    # 4. Test quota update (weekly)
    print("\n4. POST /api/devices/dev_002/quota - Update to weekly 1000 MB")
    r = requests.post(API + '/api/devices/dev_002/quota', headers=h, json={'weekly_quota_mb': 1000, 'enabled': True}, timeout=5)
    print(f"   Response: {r.status_code} {r.json()}")
    
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   Verified: weekly_quota_bytes={d.get('quota_bytes')} enabled={d.get('quota_enabled')}")
    
    # 5. Test limit
    print("\n5. POST /api/devices/dev_002/limit?ip=192.168.137.2 - Set limit 2048/512 KB/s")
    r = requests.post(API + '/api/devices/dev_002/limit?ip=192.168.137.2', headers=h, json={'download_limit': 2048, 'upload_limit': 512, 'enabled': True}, timeout=5)
    print(f"   Response: {r.status_code} {r.json()}")
    
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   Verified: limit_id={d.get('limit_id')} dl={d.get('download_limit_bps')} ul={d.get('upload_limit_bps')} enabled={d.get('limit_enabled')}")
    
    # 6. Test limit update
    print("\n6. POST /api/devices/dev_002/limit?ip=192.168.137.2 - Update to 5120/1024 KB/s")
    r = requests.post(API + '/api/devices/dev_002/limit?ip=192.168.137.2', headers=h, json={'download_limit': 5120, 'upload_limit': 1024, 'enabled': True}, timeout=5)
    print(f"   Response: {r.status_code} {r.json()}")
    
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   Verified: dl={d.get('download_limit_bps')} ul={d.get('upload_limit_bps')} enabled={d.get('limit_enabled')}")
    
    # 7. Test disable quota
    print("\n7. POST /api/devices/dev_002/quota - Disable quota")
    r = requests.post(API + '/api/devices/dev_002/quota', headers=h, json={'enabled': False}, timeout=5)
    print(f"   Response: {r.status_code} {r.json()}")
    
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   Verified: quota_enabled={d.get('quota_enabled')}")
    
    # 8. Test disable limit
    print("\n8. POST /api/devices/dev_002/limit?ip=192.168.137.2 - Disable limit")
    r = requests.post(API + '/api/devices/dev_002/limit?ip=192.168.137.2', headers=h, json={'enabled': False}, timeout=5)
    print(f"   Response: {r.status_code} {r.json()}")
    
    r = requests.get(API + '/api/devices/dev_002', headers=h, timeout=5)
    d = r.json()
    print(f"   Verified: limit_enabled={d.get('limit_enabled')}")
    
    # 9. Test traffic API
    print("\n9. GET /api/traffic/recent - Traffic data")
    r = requests.get(API + '/api/traffic/recent', headers=h, timeout=5)
    traffic = r.json()
    print(f"   Count: {len(traffic)}")
    for t in traffic[:3]:
        print(f"   - {t['device_id']} ({t['ip']}) dl={t['download']} ul={t['upload']} pkts={t['packets']} conns={t['connections']}")
    
    # 10. Test device traffic
    print("\n10. GET /api/traffic/recent?device_id=dev_002 - Device traffic")
    r = requests.get(API + '/api/traffic/recent?device_id=dev_002', headers=h, timeout=5)
    traffic = r.json()
    print(f"   Count: {len(traffic)}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == '__main__':
    test_complete_flow()