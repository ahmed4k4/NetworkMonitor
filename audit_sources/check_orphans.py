import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()

# Count devices
cur.execute("SELECT COUNT(*) FROM devices")
print("devices count:", cur.fetchone()[0])

# orphan traffic_samples
cur.execute("SELECT COUNT(*) FROM traffic_samples ts WHERE NOT EXISTS (SELECT 1 FROM devices d WHERE d.device_id = ts.device_id)")
print("orphan traffic_samples:", cur.fetchone()[0])

# distinct device_ids in traffic_samples
cur.execute("SELECT COUNT(DISTINCT device_id) FROM traffic_samples")
print("distinct device_id in traffic_samples:", cur.fetchone()[0])

# sample of device_ids in traffic_samples but not devices
cur.execute("SELECT DISTINCT ts.device_id FROM traffic_samples ts WHERE NOT EXISTS (SELECT 1 FROM devices d WHERE d.device_id = ts.device_id) LIMIT 10")
print("sample orphan device_ids:", cur.fetchall())

# Check if FK is actually enforced: try a transaction that inserts a traffic sample with a nonexistent device, and rollback
cur.execute("SELECT COUNT(*) FROM usage_daily ud WHERE NOT EXISTS (SELECT 1 FROM devices d WHERE d.device_id = ud.device_id)")
print("orphan usage_daily:", cur.fetchone()[0])

c.rollback()
return_connection(c)