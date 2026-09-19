import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        # Remove test-only records
        cur.execute("DELETE FROM device_app_usage WHERE application = 'test-integration.example.com' OR evidence::text LIKE '%test%'")
        cur.execute("DELETE FROM device_domain_usage WHERE domain = 'test-integration.example.com'")
        cur.execute("DELETE FROM dns_queries WHERE domain IN ('test-integration.example.com', 'testdomain.example.com')")
        conn.commit()
        print("Test rows cleaned")
finally:
    from database.connection import return_connection
    return_connection(conn)