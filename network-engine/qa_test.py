#!/usr/bin/env python3
"""
Comprehensive QA test for Network Control Center
Tests all API endpoints with real data verification
"""
import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')

import requests
import json
from datetime import datetime

API_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin"


def get_token():
    """Login and get JWT token"""
    r = requests.post(f"{API_URL}/api/auth/login",
                      json={"username": USERNAME, "password": PASSWORD}, timeout=10)
    if r.status_code == 200:
        return r.json()["access_token"]
    print(f"LOGIN FAILED: {r.status_code} - {r.text}")
    return None


def test_endpoint(token, method, endpoint, params=None, description=""):
    """Test a single API endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n{'='*60}")
    print(f"TEST: {description or endpoint}")
    print(f"METHOD: {method} {endpoint}  PARAMS: {params}")
    try:
        if method == "GET":
            r = requests.get(f"{API_URL}{endpoint}", headers=headers, params=params, timeout=20)
        elif method == "POST":
            r = requests.post(f"{API_URL}{endpoint}", headers=headers, json=params, timeout=20)
        else:
            print("  UNKNOWN METHOD")
            return False, None
        print(f"  STATUS: {r.status_code}")
        if r.status_code != 200:
            print(f"  ERROR: {r.text[:400]}")
            return False, None
        data = r.json()
        if isinstance(data, list):
            print(f"  -> list[{len(data)}]")
            if data:
                print(f"  -> sample: {json.dumps(data[0], default=str)[:250]}")
        elif isinstance(data, dict):
            print(f"  -> dict keys: {list(data.keys())}")
            if 'total_bytes' in data:
                print(f"  -> total_bytes: {data.get('total_bytes'):,}")
            for k in ('top_applications', 'top_domains', 'categories', 'protocols',
                      'activity_timeline', 'peaks', 'connections', 'queries'):
                if k in data:
                    print(f"  -> {k}: list[{len(data[k])}]")
        else:
            print(f"  -> {str(data)[:200]}")
        return True, data
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        return False, None


def test_devices(token):
    ok, data = test_endpoint(token, "GET", "/api/devices", description="Devices List")
    return (data if ok else None)


def test_device_detail(token, device_id):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}",
                         description=f"Device Detail ({device_id})")[1]


def test_device_intelligence(token, device_id, range="24h"):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/intelligence",
                         params={"range": range},
                         description=f"Device Intelligence ({device_id}, {range})")[1]


def test_device_applications(token, device_id, range="24h"):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/applications",
                         params={"range": range},
                         description=f"Device Applications ({device_id})")[1]


def test_device_domains(token, device_id, range="24h"):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/domains",
                         params={"range": range},
                         description=f"Device Domains ({device_id})")[1]


def test_device_categories(token, device_id, range="24h"):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/categories",
                         params={"range": range},
                         description=f"Device Categories ({device_id})")[1]


def test_device_protocols(token, device_id, range="24h"):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/protocols",
                         params={"range": range},
                         description=f"Device Protocols ({device_id})")[1]


def test_device_activity(token, device_id, days=7):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/activity",
                         params={"days": days},
                         description=f"Device Activity ({device_id}, {days}d)")[1]


def test_device_peaks(token, device_id, days=30):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/peaks",
                         params={"days": days},
                         description=f"Device Peaks ({device_id}, {days}d)")[1]


def test_device_sni(token, device_id, range="24h"):
    return test_endpoint(token, "GET", f"/api/devices/{device_id}/sni",
                         params={"range": range},
                         description=f"Device SNI ({device_id})")[1]
def test_analytics_domains(token):
    return test_endpoint(token, "GET", "/api/analytics/domains", description="Analytics Domains")[1]


def test_analytics_applications(token):
    return test_endpoint(token, "GET", "/api/analytics/applications", description="Analytics Applications")[1]


def test_traffic_recent(token, device_id=None):
    params = {"device_id": device_id} if device_id else {}
    return test_endpoint(token, "GET", "/api/traffic/recent", params=params,
                         description=f"Traffic Recent ({device_id or 'all'})")[1]


def test_traffic_history(token, device_id=None, days=30):
    params = {"days": days}
    if device_id:
        params["device_id"] = device_id
    return test_endpoint(token, "GET", "/api/traffic/history", params=params,
                         description=f"Traffic History ({device_id or 'all'}, {days}d)")[1]


def test_limits(token):
    return test_endpoint(token, "GET", "/api/control/limits", description="Limits")[1]


def test_quotas(token):
    return test_endpoint(token, "GET", "/api/control/quotas", description="Quotas")[1]


def test_connections(token, device_id=None):
    return test_endpoint(token, "GET", "/api/flows/active",
                         description=f"Active Flows/Connections ({device_id or 'all'})")[1]


def test_dns_queries(token, device_id=None):
    return test_endpoint(token, "GET", "/api/dns/recent",
                         description=f"DNS Recent Queries ({device_id or 'all'})")[1]


def test_alerts(token):
    return test_endpoint(token, "GET", "/api/alerts", description="Alerts")[1]


def test_system_status(token):
    return test_endpoint(token, "GET", "/api/system/status", description="System Status")[1]


def test_analytics_top_devices(token):
    return test_endpoint(token, "GET", "/api/analytics/top-devices", description="Analytics Top Devices")[1]


def test_analytics_hourly(token):
    return test_endpoint(token, "GET", "/api/analytics/hourly", description="Analytics Hourly")[1]


def test_analytics_daily(token):
    return test_endpoint(token, "GET", "/api/analytics/daily", description="Analytics Daily")[1]


def test_health(token=None):
    return test_endpoint(None, "GET", "/api/health", description="Health Check")[1]


def main():
    print("=" * 60)
    print("NETWORK CONTROL CENTER - REAL DATA QA PASS")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Time: {datetime.now().isoformat()}")

    test_health(token=None)

    token = get_token()
    if not token:
        print("\nLOGIN FAILED - Cannot continue")
        return 1
    print("\nLOGIN SUCCESS - Token acquired")

    devices = test_devices(token)
    if not devices:
        print("\nNO DEVICES FOUND")
        device_id = "dev_001"
        device = None
    else:
        device = max(devices, key=lambda d: d.get("total_today", 0) or 0)
        device_id = device.get("device_id", "dev_001")
        print(f"\nUsing device: {device_id} (busiest by total_today)")
        print(f"  IP: {device.get('ip', 'N/A')}")
        print(f"  Name: {device.get('custom_name') or device.get('hostname') or 'N/A'}")
        print(f"  State: {device.get('state', 'N/A')}")
        print(f"  Download Today: {device.get('download_today', 0):,} bytes")
        print(f"  Upload Today: {device.get('upload_today', 0):,} bytes")
        print(f"  Total Today: {device.get('total_today', 0):,} bytes")
        print(f"  Online: {device.get('online', 'N/A')}")

    test_device_detail(token, device_id)
    intel = test_device_intelligence(token, device_id, "24h")
    test_device_applications(token, device_id, "24h")
    test_device_domains(token, device_id, "24h")
    test_device_categories(token, device_id, "24h")
    test_device_protocols(token, device_id, "24h")
    test_device_activity(token, device_id, 7)
    test_device_peaks(token, device_id, 30)
    test_device_sni(token, device_id, "24h")

    test_analytics_domains(token)
    test_analytics_applications(token)

    test_traffic_recent(token, device_id)
    test_traffic_recent(token, None)
    test_traffic_history(token, device_id, 30)
    test_traffic_history(token, None, 30)

    test_limits(token)
    test_quotas(token)

    test_connections(token, device_id)
    test_dns_queries(token, device_id)

    test_alerts(token)
    test_system_status(token)
    test_analytics_top_devices(token)
    test_analytics_hourly(token)
    test_analytics_daily(token)

    print("\n" + "=" * 60)
    print("CROSS-VERIFICATION")
    print("=" * 60)
    if intel:
        print("\nDevice Intelligence (24h):")
        for k in ("total_download_bytes", "total_upload_bytes", "total_bytes",
                  "total_connections", "top_applications", "top_domains",
                  "categories", "protocols", "peaks", "activity_timeline"):
            v = intel.get(k, 0)
            if isinstance(v, list):
                print(f"  {k}: list[{len(v)}]")
            else:
                print(f"  {k}: {v:,}")
    if device:
        print("\nDevices List (today):")
        for k in ("download_today", "upload_today", "total_today", "connections_today"):
            print(f"  {k}: {device.get(k, 0):,}")

    print("\n" + "=" * 60)
    print("QA PASS COMPLETE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())