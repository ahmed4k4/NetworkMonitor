import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.connection import get_connection

c = get_connection()
print("=== device_app_usage sample ===")
rows = c.execute(
    "SELECT * FROM device_app_usage ORDER BY 1 DESC LIMIT 5"
).fetchall()
cols = [d[0] for d in c.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='device_app_usage' ORDER BY ordinal_position"
).description]
# description may be on cursor; simpler: query columns separately
c2 = get_connection()
colrows = c2.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='device_app_usage' ORDER BY ordinal_position"
).fetchall()
cols = [r[0] for r in colrows]
print("columns:", cols)
for r in rows:
    print("  ", r)

print()
print("=== distinct apps in device_app_usage ===")
rows = c.execute(
    "SELECT app_name, COUNT(*) FROM device_app_usage GROUP BY app_name ORDER BY 2 DESC LIMIT 10"
).fetchall()
for r in rows:
    print("  ", r)

c.close()
c2.close()