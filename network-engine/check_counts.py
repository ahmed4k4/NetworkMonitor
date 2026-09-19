import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM flows')
        print('Flows:', cur.fetchone()[0])
        cur.execute('SELECT COUNT(*) FROM traffic_samples')
        print('Traffic samples:', cur.fetchone()[0])
        cur.execute('SELECT COUNT(*) FROM dns_queries')
        print('DNS queries:', cur.fetchone()[0])
finally:
    from database.connection import return_connection
    return_connection(conn)