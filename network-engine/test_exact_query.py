import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        print("--- exact repo query ---")
        cur.execute(
            """
            SELECT domain, category, confidence,
                   SUM(download_bytes) as download_bytes,
                   SUM(upload_bytes) as upload_bytes,
                   SUM(total_bytes) as total_bytes,
                   SUM(queries) as queries,
                   SUM(connections) as connections,
                   (array_agg(evidence ORDER BY total_bytes DESC))[1] as evidence
            FROM device_domain_usage
            WHERE device_id = %s
              AND hour_start > NOW() - INTERVAL '%s hours'
            GROUP BY domain, category, confidence
            ORDER BY total_bytes DESC
            LIMIT %s
            """,
            ('dev_001', 24, 50)
        )
        rows = cur.fetchall()
        print("rows:", len(rows))
        for r in rows[:5]:
            print(r)
finally:
    from database.connection import return_connection
    return_connection(conn)