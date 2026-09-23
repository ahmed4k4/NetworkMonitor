import psycopg2

conn = psycopg2.connect(host="localhost", dbname="network_control", user="postgres", password="12345678")
cur = conn.cursor()

cur.execute(
    "SELECT to_char(last_seen, 'YYYY-MM-DD HH24:MI'), total_upload, total_download, total_packets "
    "FROM devices WHERE device_id = %s",
    ("dev_002",),
)
print("dev_002 devices:", cur.fetchone())

cur.execute(
    "SELECT count(*), min(sampled_at), max(sampled_at), "
    "coalesce(sum(download_bytes),0), coalesce(sum(upload_bytes),0), coalesce(sum(packets),0) "
    "FROM traffic_samples WHERE device_id = %s",
    ("dev_002",),
)
print("dev_002 traffic_samples:", cur.fetchone())

cur.execute(
    "SELECT count(*), coalesce(sum(download_bytes),0), coalesce(sum(upload_bytes),0) "
    "FROM usage_daily WHERE device_id = %s",
    ("dev_002",),
)
print("dev_002 usage_daily:", cur.fetchone())

cur.execute(
    "SELECT direction, count(*), coalesce(sum(download_bytes),0), coalesce(sum(upload_bytes),0) "
    "FROM flows WHERE device_id = %s GROUP BY direction",
    ("dev_002",),
)
print("dev_002 flows by direction:", cur.fetchall())

cur.execute(
    "SELECT count(*) FROM flows WHERE device_id = %s AND started_at >= now() - interval '1 day'",
    ("dev_002",),
)
print("dev_002 flows last 24h:", cur.fetchone())

cur.close()
conn.close()
