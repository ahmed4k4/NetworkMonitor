import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import psycopg
from config import database_config as dc

def db():
    return psycopg.connect(host=dc.host, port=dc.port, dbname=dc.database, user=dc.user, password=dc.password)

c = db()
cur = c.cursor()

print("=== ALL TABLES ===")
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
for r in cur.fetchall():
    print("  ", r[0])

def count(t):
    cur.execute(f"SELECT count(*) FROM {t}")
    return cur.fetchone()[0]

c.commit()

print("\n=== traffic_samples (latest 10) ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='traffic_samples' ORDER BY ordinal_position")
samp_cols = [r[0] for r in cur.fetchall()]
print("  cols:", samp_cols)
c.commit()
try:
    cur.execute("SELECT * FROM traffic_samples ORDER BY " + samp_cols[0] + " DESC LIMIT 10")
    rows = cur.fetchall()
    for r in rows:
        print("  ", r)
except Exception as e:
    print("  err:", e)
    c.rollback()
c.commit()

c.commit()

print("\n=== flows for dev_002 (latest 5) ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='flows' ORDER BY ordinal_position")
print("  cols:", [r[0] for r in cur.fetchall()])
try:
    cur.execute("SELECT * FROM flows WHERE device_id='dev_002' ORDER BY flow_time DESC LIMIT 5")
    for r in cur.fetchall():
        print("  ", r)
except Exception as e:
    print("  err:", e)
    c.rollback()

c.commit()

print("\n=== realtime watch: device totals over 12s ===")
def snapshot():
    cur.execute("SELECT total_upload, total_download, total_packets, last_seen, state FROM devices WHERE device_id='dev_002'")
    return cur.fetchone()
    c.commit()

a = snapshot(); print("  t0:", a); time.sleep(12)
b = snapshot(); print("  t1:", b)
if b and a and (b[0] != a[0] or b[1] != a[1] or b[2] != a[2]):
    print("  METRICS ARE MOVING")
else:
    print("  metrics static over 12s")
c.close()