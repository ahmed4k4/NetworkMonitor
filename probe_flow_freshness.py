import io, sys, psycopg
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
from config import database_config

c = psycopg.connect(host=database_config.host, port=database_config.port,
                    dbname=database_config.database, user=database_config.user,
                    password=database_config.password, autocommit=True)
cur = c.cursor()

cur.execute("SELECT device_id, MAX(started_at), MAX(last_seen), COUNT(*) FROM flows GROUP BY device_id ORDER BY device_id")
print("FLOWS per device (max started_at, max last_seen, count):")
for r in cur.fetchall():
    print("  ", r)

cur.execute("SELECT NOW()")
print("NOW() =", cur.fetchone()[0])
c.close()