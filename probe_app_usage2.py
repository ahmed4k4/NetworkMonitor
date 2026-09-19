import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.connection import get_connection

c = get_connection()

print("=== distinct application values in device_app_usage ===")
rows = c.execute(
    "SELECT application, confidence, COUNT(*) FROM device_app_usage "
    "GROUP BY application, confidence ORDER BY 3 DESC LIMIT 10"
).fetchall()
for r in rows:
    print("  ", r)

print()
print("=== rows where application != 'Unknown' ===")
rows = c.execute(
    "SELECT application, category, confidence, evidence FROM device_app_usage "
    "WHERE application IS NOT NULL AND application != 'Unknown' LIMIT 10"
).fetchall()
print("  count:", len(rows))
for r in rows:
    print("  ", r)

print()
print("=== device_activity_timeline sample ===")
rows = c.execute(
    "SELECT * FROM device_activity_timeline ORDER BY 1 DESC LIMIT 3"
).fetchall()
colrows = c.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='device_activity_timeline' ORDER BY ordinal_position"
).fetchall()
print("columns:", [r[0] for r in colrows])
for r in rows:
    print("  ", r)

c.close()