import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import psycopg
from config import database_config as dc
c = psycopg.connect(host=dc.host, port=dc.port, dbname=dc.database, user=dc.user, password=dc.password)
c.autocommit = False
cur = c.cursor()

DEV = "dev_002"
UPD = 50
DLN = 100
PKT = 3

# 1. Show current state before revert
cur.execute("SELECT total_upload, total_download, total_packets FROM devices WHERE device_id=%s", (DEV,))
print("devices before:", cur.fetchone())
cur.execute("SELECT download_bytes, upload_bytes, packets FROM usage_daily WHERE device_id=%s AND day_start=(NOW() AT TIME ZONE 'Africa/Cairo')::date", (DEV,))
print("usage_daily today before:", cur.fetchone())
cur.execute("SELECT count(*) FROM traffic_samples WHERE device_id=%s", (DEV,))
print("samples before:", cur.fetchone()[0])

# 2. Delete the probe sample row (dev_002 with download=100 upload=50 packets=3 sampled ~4:47 GMT)
cur.execute(
    "DELETE FROM traffic_samples WHERE device_id=%s AND download_bytes=%s AND upload_bytes=%s AND packets=%s",
    (DEV, DLN, UPD, PKT),
)
print("deleted rows:", cur.rowcount)

# 3. Revert device totals
cur.execute(
    "UPDATE devices SET total_upload=GREATEST(total_upload - %s,0), total_download=GREATEST(total_download - %s,0), total_packets=GREATEST(total_packets - %s,0) WHERE device_id=%s",
    (UPD, DLN, PKT, DEV),
)

# 4. Revert daily/hourly/monthly aggregates
cur.execute(
    "UPDATE usage_daily SET download_bytes=GREATEST(download_bytes-%s,0), upload_bytes=GREATEST(upload_bytes-%s,0), packets=GREATEST(packets-%s,0) WHERE device_id=%s AND day_start=(NOW() AT TIME ZONE 'Africa/Cairo')::date",
    (DLN, UPD, PKT, DEV),
)
cur.execute(
    "UPDATE usage_hourly SET download_bytes=GREATEST(download_bytes-%s,0), upload_bytes=GREATEST(upload_bytes-%s,0), packets=GREATEST(packets-%s,0) WHERE device_id=%s AND hour_start=date_trunc('hour', NOW())",
    (DLN, UPD, PKT, DEV),
)
cur.execute(
    "UPDATE usage_monthly SET download_bytes=GREATEST(download_bytes-%s,0), upload_bytes=GREATEST(upload_bytes-%s,0), packets=GREATEST(packets-%s,0) WHERE device_id=%s AND month_start=date_trunc('month', CURRENT_DATE)::date",
    (DLN, UPD, PKT, DEV),
)

# 5. Revert data_limits used_bytes (it was recomputed from usage_daily)
cur.execute("UPDATE data_limits SET used_bytes=GREATEST(used_bytes-%s,0) WHERE device_id=%s", (DLN+UPD, DEV))

c.commit()

cur.execute("SELECT total_upload, total_download, total_packets FROM devices WHERE device_id=%s", (DEV,))
print("devices after:", cur.fetchone())
cur.execute("SELECT count(*) FROM traffic_samples WHERE device_id=%s", (DEV,))
print("samples after:", cur.fetchone()[0])