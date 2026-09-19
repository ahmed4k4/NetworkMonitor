import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import psycopg
from config import database_config as dc

c = psycopg.connect(host=dc.host, port=dc.port, dbname=dc.database, user=dc.user, password=dc.password)
cur = c.cursor()

print("=== flows last 300s (with device_id) ===")
cur.execute("""
    SELECT id, device_id, source_ip, destination_ip, source_port, destination_port,
           protocol, direction, started_at, last_seen, packets, bytes, upload_bytes, download_bytes, state
    FROM flows
    WHERE last_seen >= now() - interval '300 seconds'
    ORDER BY last_seen DESC
    LIMIT 40
""")
rows = cur.fetchall()
print("count:", len(rows))
for r in rows:
    print("  ", r)
c.commit()

print("\n=== flows for dev_002 (any time, latest 15) ===")
cur.execute("""
    SELECT id, device_id, source_ip, destination_ip, source_port, destination_port,
           protocol, direction, started_at, last_seen, packets, bytes, upload_bytes, download_bytes, state
    FROM flows
    WHERE device_id='dev_002'
    ORDER BY last_seen DESC NULLS LAST
    LIMIT 15
""")
for r in cur.fetchall():
    print("  ", r)
c.commit()

print("\n=== connections (device_id distinct, latest) ===")
try:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='connections' ORDER BY ordinal_position")
    print("  conns cols:", [r[0] for r in cur.fetchall()])
    c.commit()
    cur.execute("SELECT * FROM connections ORDER BY 1 DESC LIMIT 20")
    for r in cur.fetchall():
        print("  ", r)
except Exception as e:
    print("  err:", e)
c.close()