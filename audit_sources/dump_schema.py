import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection

tables = [
    'devices', 'flows', 'traffic_samples', 'connections',
    'device_app_usage', 'device_domain_usage', 'device_category_usage',
    'device_protocol_usage', 'usage_hourly', 'usage_daily', 'usage_monthly',
    'dns_queries', 'sni_observations', 'device_peaks', 'device_activity_timeline',
    'speed_limits', 'data_limits',
]

c = get_connection()
cur = c.cursor()
for t in tables:
    cur.execute(
        "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns "
        "WHERE table_name=%s ORDER BY ordinal_position", (t,))
    rows = cur.fetchall()
    print(f"\n=== {t} ===")
    if not rows:
        print("  (MISSING)")
    for name, dtype, nullable, default in rows:
        print(f"  {name} {dtype} nullable={nullable} default={default}")
return_connection(c)