import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM devices WHERE device_id = 'dev_001'")
        print('dev_001 exists:', cur.fetchone()[0] > 0)
        cur.execute("SELECT device_id FROM devices LIMIT 5")
        print('sample device ids:', [r[0] for r in cur.fetchall()])
finally:
    return_connection(conn)