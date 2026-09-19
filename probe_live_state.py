import sys, io, json, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import psycopg
from config import database_config as dc

def db():
    return psycopg.connect(host=dc.host, port=dc.port, dbname=dc.database, user=dc.user, password=dc.password)

c = db()
cur = c.cursor()

print("=== DEVICES SCHEMA ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='devices' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("  cols:", cols)

print("=== DEVICES ===")
cur.execute("SELECT * FROM devices ORDER BY last_seen DESC NULLS LAST LIMIT 20")
for r in cur.fetchall():
    print(" ", r)

print("=== TABLES COUNTS ===")
for t in ["devices", "traffic_samples", "flows", "applications", "domains", "activity_events", "peaks", "usage_daily", "usage_hourly", "usage_monthly"]:
    try:
        cur.execute(f"SELECT count(*) FROM {t}")
        print(f"  {t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"  {t}: ERROR {e}")
c.close()