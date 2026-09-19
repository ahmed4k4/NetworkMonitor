import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        print("NOW():")
        cur.execute("SELECT NOW(), NOW() AT TIME ZONE 'Africa/Cairo'")
        print(cur.fetchone())

        print("\nAll device_domain_usage rows:")
        cur.execute("""
            SELECT device_id, domain, hour_start::text, queries, confidence
            FROM device_domain_usage
            ORDER BY hour_start DESC
        """)
        for row in cur.fetchall():
            print(" ", row)

        print("\nMidnight-UTC rows for dev_001:")
        cur.execute("""
            SELECT device_id, domain, hour_start::text
            FROM device_domain_usage
            WHERE device_id = 'dev_001'
        """)
        for row in cur.fetchall():
            print(" ", row)

        print("\nRows with hour_start > NOW() - interval '24 hours':")
        cur.execute("""
            SELECT device_id, domain, hour_start::text
            FROM device_domain_usage
            WHERE hour_start > NOW() - INTERVAL '24 hours'
        """)
        for row in cur.fetchall():
            print(" ", row)
finally:
    from database.connection import return_connection
    return_connection(conn)