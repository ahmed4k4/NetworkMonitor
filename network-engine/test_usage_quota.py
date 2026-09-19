#!/usr/bin/env python
"""
Test: Device Usage Data + Quota/Limit Management
Verifies:
1. Devices endpoint returns real usage data (download_today, upload_today, speeds)
2. Setting a quota persists to database
3. Setting a limit persists to database
4. Changes are immediately reflected in the devices endpoint
"""

import requests
import json
import sys
import time

API_BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/auth/login"
DEVICES_ENDPOINT = f"{API_BASE_URL}/api/devices"
QUOTAS_ENDPOINT = f"{API_BASE_URL}/api/control/quotas"
LIMITS_ENDPOINT = f"{API_BASE_URL}/api/control/limits"

USERNAME = "admin"
PASSWORD = "admin_change_me"


def login():
    """Login and get JWT token"""
    response = requests.post(
        LOGIN_ENDPOINT,
        json={"username": USERNAME, "password": PASSWORD},
        timeout=5,
    )
    if response.status_code != 200:
        print(f"✗ Login failed: {response.status_code} {response.text}")
        return None
    token = response.json().get("access_token")
    print(f"✓ Login successful, token obtained")
    return {"Authorization": f"Bearer {token}"}


def test_devices_usage(headers):
    """Test that devices endpoint returns real usage data"""
    print("\n" + "=" * 70)
    print("TEST 1: Devices endpoint returns real usage data")
    print("=" * 70)

    response = requests.get(DEVICES_ENDPOINT, headers=headers, timeout=5)
    if response.status_code != 200:
        print(f"✗ Failed to get devices: {response.status_code} {response.text}")
        return None

    devices = response.json()
    print(f"✓ Got {len(devices)} devices")

    if not devices:
        print("⚠ No devices found - cannot verify usage data")
        return None

    device = devices[0]
    device_id = device.get("device_id")
    print(f"\nDevice: {device_id}")
    print(f"  - download_today: {device.get('download_today')}")
    print(f"  - upload_today: {device.get('upload_today')}")
    print(f"  - total_today: {device.get('total_today')}")
    print(f"  - download_speed_bps: {device.get('download_speed_bps')}")
    print(f"  - upload_speed_bps: {device.get('upload_speed_bps')}")
    print(f"  - current_speed_bps: {device.get('current_speed_bps')}")
    print(f"  - usage_percentage: {device.get('usage_percentage')}")
    print(f"  - quota_bytes: {device.get('quota_bytes')}")
    print(f"  - quota_used_bytes: {device.get('quota_used_bytes')}")
    print(f"  - quota_remaining_bytes: {device.get('quota_remaining_bytes')}")
    print(f"  - limit_id: {device.get('limit_id')}")
    print(f"  - download_limit_bps: {device.get('download_limit_bps')}")
    print(f"  - upload_limit_bps: {device.get('upload_limit_bps')}")

    # Verify usage fields exist
    required_fields = [
        "download_today", "upload_today", "total_today",
        "download_speed_bps", "upload_speed_bps", "current_speed_bps",
        "usage_percentage", "quota_bytes", "quota_used_bytes",
        "quota_remaining_bytes", "quota_enabled",
        "limit_id", "download_limit_bps", "upload_limit_bps", "limit_enabled",
    ]
    missing = [f for f in required_fields if f not in device]
    if missing:
        print(f"✗ Missing fields: {missing}")
        return None

    print("✓ All usage data fields present")
    return device_id


def test_set_quota(headers, device_id):
    """Test setting a quota and verifying it persists"""
    print("\n" + "=" * 70)
    print("TEST 2: Set quota and verify persistence")
    print("=" * 70)

    # Set a daily quota of 2048 MB
    quota_payload = {
        "daily_quota_mb": 2048,
        "weekly_quota_mb": 14336,
        "monthly_quota_mb": 61440,
        "enabled": True,
    }

    response = requests.post(
        f"{DEVICES_ENDPOINT}/{device_id}/quota",
        headers=headers,
        json=quota_payload,
        timeout=5,
    )
    if response.status_code != 200:
        print(f"✗ Failed to set quota: {response.status_code} {response.text}")
        return False

    result = response.json()
    print(f"✓ Quota set: {json.dumps(result, indent=2)}")

    # Verify quota is persisted by fetching devices again
    time.sleep(0.5)
    response = requests.get(DEVICES_ENDPOINT, headers=headers, timeout=5)
    devices = response.json()
    device = next((d for d in devices if d["device_id"] == device_id), None)

    if not device:
        print(f"✗ Device {device_id} not found after quota set")
        return False

    expected_daily = 2048 * 1024 * 1024  # 2048 MB in bytes
    actual_quota = device.get("quota_bytes")
    print(f"  Expected quota_bytes: {expected_daily}")
    print(f"  Actual quota_bytes: {actual_quota}")

    if actual_quota == expected_daily:
        print("✓ Quota persisted and reflected in devices endpoint")
        return True
    else:
        print(f"✗ Quota mismatch! Expected {expected_daily}, got {actual_quota}")
        return False


def test_set_limit(headers, device_id):
    """Test setting a speed limit and verifying it persists"""
    print("\n" + "=" * 70)
    print("TEST 3: Set speed limit and verify persistence")
    print("=" * 70)

    # Get device IP first
    response = requests.get(DEVICES_ENDPOINT, headers=headers, timeout=5)
    devices = response.json()
    device = next((d for d in devices if d["device_id"] == device_id), None)
    if not device:
        print(f"✗ Device {device_id} not found")
        return False

    ip = device.get("ip", "")
    print(f"  Device IP: {ip}")

    # Set download limit to 5120 KB/s and upload to 1024 KB/s
    limit_payload = {
        "download_limit": 5120,
        "upload_limit": 1024,
        "enabled": True,
    }

    response = requests.post(
        f"{DEVICES_ENDPOINT}/{device_id}/limit?ip={ip}",
        headers=headers,
        json=limit_payload,
        timeout=5,
    )
    if response.status_code != 200:
        print(f"✗ Failed to set limit: {response.status_code} {response.text}")
        return False

    result = response.json()
    print(f"✓ Limit set: {json.dumps(result, indent=2)}")

    # Verify limit is persisted by fetching devices again
    time.sleep(0.5)
    response = requests.get(DEVICES_ENDPOINT, headers=headers, timeout=5)
    devices = response.json()
    device = next((d for d in devices if d["device_id"] == device_id), None)

    if not device:
        print(f"✗ Device {device_id} not found after limit set")
        return False

    expected_dl = 5120 * 1024 * 8  # 5120 KB/s in bps
    expected_ul = 1024 * 1024 * 8  # 1024 KB/s in bps
    actual_dl = device.get("download_limit_bps")
    actual_ul = device.get("upload_limit_bps")
    print(f"  Expected download_limit_bps: {expected_dl}")
    print(f"  Actual download_limit_bps: {actual_dl}")
    print(f"  Expected upload_limit_bps: {expected_ul}")
    print(f"  Actual upload_limit_bps: {actual_ul}")

    if actual_dl == expected_dl and actual_ul == expected_ul:
        print("✓ Limit persisted and reflected in devices endpoint")
        return True
    else:
        print(f"✗ Limit mismatch! Expected DL={expected_dl}, UL={expected_ul}, got DL={actual_dl}, UL={actual_ul}")
        return False


def test_quotas_endpoint(headers, device_id):
    """Test the control quotas endpoint"""
    print("\n" + "=" * 70)
    print("TEST 4: Control quotas endpoint")
    print("=" * 70)

    response = requests.get(QUOTAS_ENDPOINT, headers=headers, timeout=5)
    if response.status_code != 200:
        print(f"✗ Failed to get quotas: {response.status_code} {response.text}")
        return False

    quotas = response.json()
    print(f"✓ Got {len(quotas)} quotas")
    for quota in quotas:
        if quota.get("device_id") == device_id:
            print(f"  Found quota for device: {json.dumps(quota, indent=2)}")
            return True

    print(f"✗ Quota for device {device_id} not found in control endpoint")
    return False


def test_limits_endpoint(headers, device_id):
    """Test the control limits endpoint"""
    print("\n" + "=" * 70)
    print("TEST 5: Control limits endpoint")
    print("=" * 70)

    response = requests.get(LIMITS_ENDPOINT, headers=headers, timeout=5)
    if response.status_code != 200:
        print(f"✗ Failed to get limits: {response.status_code} {response.text}")
        return False

    limits = response.json()
    print(f"✓ Got {len(limits)} limits")
    for limit in limits:
        if limit.get("device_id") == device_id:
            print(f"  Found limit for device: {json.dumps(limit, indent=2)}")
            return True

    print(f"✗ Limit for device {device_id} not found in control endpoint")
    return False


def main():
    print("=" * 70)
    print("DEVICE USAGE + QUOTA/LIMIT MANAGEMENT TEST")
    print("=" * 70)

    headers = login()
    if not headers:
        return False

    device_id = test_devices_usage(headers)
    if not device_id:
        print("⚠ Cannot proceed without a device")
        return False

    results = []
    results.append(("Set Quota", test_set_quota(headers, device_id)))
    results.append(("Set Limit", test_set_limit(headers, device_id)))
    results.append(("Quotas Endpoint", test_quotas_endpoint(headers, device_id)))
    results.append(("Limits Endpoint", test_limits_endpoint(headers, device_id)))

    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)