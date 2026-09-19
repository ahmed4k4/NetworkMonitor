import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.connection import get_connection

c = get_connection()
cur = c.cursor()
cur.execute(
    "SELECT app_name, COUNT(*) FROM flows WHERE app_name IS NOT NULL AND app_name != '' "
    "GROUP BY app_name ORDER BY 2 DESC LIMIT 8"
)
rows = cur.fetchall()
print("DISTINCT attributed apps in flows:", len(rows))
for r in rows:
    print("  ", r)
cur.execute("SELECT COUNT(*) FROM flows")
print("total flows:", cur.fetchone()[0])

# Also count flows with domain evidence to justify domains=49
cur.execute(
    "SELECT COUNT(*) FROM flows WHERE domain IS NOT NULL AND domain != ''"
)
print("flows with domain evidence:", cur.fetchone()[0])
c.close()