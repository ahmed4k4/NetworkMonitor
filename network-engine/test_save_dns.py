import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection
from database.repository import DeviceIntelligenceRepository

repo = DeviceIntelligenceRepository()

# Test saving a DNS query
try:
    repo.save_dns_query("dev_001", "google.com", "A")
    print("save_dns_query executed successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Check if it was saved
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM dns_queries ORDER BY queried_at DESC LIMIT 5')
        for row in cur.fetchall():
            print(row)
finally:
    from database.connection import return_connection
    return_connection(conn)