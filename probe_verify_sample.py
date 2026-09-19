import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import psycopg
from config import database_config as dc
c = psycopg.connect(host=dc.host, port=dc.port, dbname=dc.database, user=dc.user, password=dc.password)
cur = c.cursor()
cur.execute("SELECT count(*) FROM traffic_samples")
print("traffic_samples n:", cur.fetchone()[0])
cur.execute("SELECT device_id, download_bytes, upload_bytes, packets, download_speed_bps, upload_speed_bps, sampled_at FROM traffic_samples ORDER BY sampled_at DESC LIMIT 3")
for r in cur.fetchall():
    print(" row:", r)