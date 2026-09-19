import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('SELECT device_id, COUNT(*) FROM device_domain_usage GROUP BY device_id')
        print('device_domain_usage:', cur.fetchall())
        cur.execute('SELECT device_id, COUNT(*) FROM device_app_usage GROUP BY device_id')
        print('device_app_usage:', cur.fetchall())
finally:
    from database.connection import return_connection
    return_connection(conn)