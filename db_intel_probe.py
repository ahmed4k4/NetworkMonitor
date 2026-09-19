import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
cur = conn.cursor()

# List intelligence-related tables
cur.execute("""
SELECT table_name FROM information_schema.tables
WHERE table_schema='public'
ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]
print("=== ALL TABLES ===")
for t in tables:
    print(t)

print()
print("=== ROW COUNTS FOR INTELLIGENCE TABLES ===")
for t in ['device_app_usage','device_domain_usage','device_category_usage',
          'device_protocol_usage','device_peaks','device_activity_timeline',
          'sni_observations','traffic_samples','devices','flows']:
    if t in tables:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        n = cur.fetchone()[0]
        print(f"{t}: {n}")
    else:
        print(f"{t}: MISSING")

conn.close()