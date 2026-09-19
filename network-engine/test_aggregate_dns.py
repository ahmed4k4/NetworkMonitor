import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.repository import DeviceIntelligenceRepository
from database.connection import get_connection

repo = DeviceIntelligenceRepository()
count = repo.aggregate_dns_domains(hours=48)
print("Upserted domain usage rows:", count)

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT device_id, domain, queries, confidence, total_bytes,
                   hour_start::text, category
            FROM device_domain_usage
            ORDER BY queries DESC
            LIMIT 20
        """)
        for row in cur.fetchall():
            print(row)
finally:
    from database.connection import return_connection
    return_connection(conn)