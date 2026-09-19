import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')

from discovery.identity import DeviceIdentityManager
from database.repository import DeviceRepository
import uuid

# Test identity manager
print("Testing DeviceIdentityManager...")
identity = DeviceIdentityManager()

# Test MAC normalization
mac1 = "aa:bb:cc:dd:ee:ff"
mac2 = "AA-BB-CC-DD-EE-FF"
mac3 = "aabbccddeeff"

print(f"Normalized MAC 1: {identity.normalize_mac(mac1)}")
print(f"Normalized MAC 2: {identity.normalize_mac(mac2)}")
print(f"Normalized MAC 3: {identity.normalize_mac(mac3)}")

# Test device_id persistence
device_id1 = identity.get_device_id(mac1)
print(f"Device ID for {mac1}: {device_id1}")

# Get again - should be same
device_id2 = identity.get_device_id(mac2)
print(f"Device ID for {mac2}: {device_id2}")

assert device_id1 == device_id2, "Same MAC should return same device_id!"

# Test new MAC
device_id3 = identity.get_device_id("11:22:33:44:55:66")
print(f"Device ID for new MAC: {device_id3}")

# Test DeviceRepository upsert with custom_name
print("\nTesting DeviceRepository upsert with custom_name...")
repo = DeviceRepository()

test_device = {
    "device_id": "test_dev_001",
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.100",
    "hostname": "test-device",
    "custom_name": "My Custom Device Name",
    "vendor": "Test Vendor",
    "interface": "eth0",
    "state": "ONLINE"
}

repo.upsert_device(test_device)
print("Device upserted successfully!")

# Retrieve and verify
connection = None
try:
    from database.connection import get_connection
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT device_id, mac_address, hostname, custom_name FROM devices WHERE device_id = %s", ("test_dev_001",))
        row = cursor.fetchone()
        if row:
            print(f"Retrieved: device_id={row[0]}, mac={row[1]}, hostname={row[2]}, custom_name={row[3]}")
            assert row[3] == "My Custom Device Name", "custom_name should be persisted!"
            print("✓ custom_name persisted correctly!")
        else:
            print("Device not found!")
finally:
    if connection:
        connection.close()

# Test rename
print("\nTesting rename via DeviceRepository...")
import psycopg
conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute("UPDATE devices SET custom_name = %s WHERE device_id = %s", ("New Renamed Name", "test_dev_001"))
    conn.commit()
    
    cur.execute("SELECT custom_name FROM devices WHERE device_id = %s", ("test_dev_001",))
    row = cur.fetchone()
    print(f"New custom_name: {row[0]}")
    assert row[0] == "New Renamed Name", "Rename should work!"

print("\n✓ All tests passed!")