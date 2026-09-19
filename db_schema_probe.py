import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
cur = conn.cursor()

for t in ['device_app_usage','device_domain_usage','device_category_usage',
          'device_protocol_usage','device_peaks','device_activity_timeline',
          'sni_observations','dns_queries']:
    print(f"=== {t} columns ===")
    cur.execute("""
    SELECT column_name, data_type FROM information_schema.columns
    WHERE table_name=%s ORDER BY ordinal_position
    """, (t,))
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")
    print()

conn.close()