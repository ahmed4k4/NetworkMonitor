import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from datetime import timedelta
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT NOW() - %s", (timedelta(hours=24),))
        a = cur.fetchone()[0]
        cur.execute("SELECT NOW() - INTERVAL '24 hours'")
        b = cur.fetchone()[0]
        print("timedelta interval:", a)
        print("literal interval:  ", b)
        print("equal:", abs((a - b).total_seconds()) < 1)
finally:
    from database.connection import return_connection
    return_connection(conn)