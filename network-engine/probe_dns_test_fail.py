import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.repository import DeviceIntelligenceRepository
from database.connection import get_connection, return_connection

repo = DeviceIntelligenceRepository()
test_domain = "auditprobe.example.com"
print("devices table check:")
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT device_id, hostname FROM devices WHERE device_id = 'dev_001'")
        print("  dev_001:", cur.fetchall())
        cur.execute("SELECT count(*) FROM devices")
        print("  total devices:", cur.fetchone())
finally:
    return_connection(conn)

try:
    repo.save_dns_query("dev_001", test_domain, "A", response_ip="203.0.113.50")
    print("save_dns_query call returned (no exception)")
except Exception as e:
    print("save_dns_query RAISED:", type(e).__name__, e)

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT device_id, domain, response_ip::text FROM dns_queries WHERE domain = %s",
            (test_domain,),
        )
        print("rows after save:", cur.fetchall())
finally:
    return_connection(conn)