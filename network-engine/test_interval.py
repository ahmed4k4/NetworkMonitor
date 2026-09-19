import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT NOW() - INTERVAL '%s hours'", (24,))
        a = cur.fetchone()[0]
        cur.execute("SELECT NOW() - INTERVAL '24 hours'")
        b = cur.fetchone()[0]
        print("param interval:", a)
        print("literal interval:", b)
        print("equal:", abs((a - b).total_seconds()) < 1)

        cur.execute("SELECT %s::text", ("SELECT NOW() - INTERVAL '%s hours', (24,)",))
        # Show what psycopg sends by making a query that exposes it
        cur.execute("SELECT INTERVAL '%s hours'::text", (24,))
        print("interval text:", cur.fetchone()[0])
finally:
    from database.connection import return_connection
    return_connection(conn)