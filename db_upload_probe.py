import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
cur = conn.cursor()

print("=== usage_daily today ===")
cur.execute("""
SELECT device_id, day_start, download_bytes, upload_bytes
FROM usage_daily
ORDER BY day_start DESC
LIMIT 30
""")
for r in cur.fetchall():
    print(r)

print()
print("=== flows columns ===")
cur.execute("""
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='flows' ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(r)

print()
print("=== flows sample (latest 10) ===")
cur.execute("""
SELECT device_id, source_ip, destination_ip, source_port, destination_port,
       protocol, direction, bytes, upload_bytes, download_bytes,
       started_at, last_seen
FROM flows
ORDER BY last_seen DESC
LIMIT 10
""")
for r in cur.fetchall():
    print(r)

print()
print("=== flow direction: src vs dst for dev_002 (phone 192.168.137.2) ===")
cur.execute("""
SELECT
  SUM(CASE WHEN source_ip::text = '192.168.137.2' THEN COALESCE(upload_bytes,0) ELSE 0 END) AS phone_src_upload,
  SUM(CASE WHEN source_ip::text = '192.168.137.2' THEN COALESCE(download_bytes,0) ELSE 0 END) AS phone_src_download,
  SUM(CASE WHEN destination_ip::text = '192.168.137.2' THEN COALESCE(upload_bytes,0) ELSE 0 END) AS phone_dst_upload,
  SUM(CASE WHEN destination_ip::text = '192.168.137.2' THEN COALESCE(download_bytes,0) ELSE 0 END) AS phone_dst_download,
  COUNT(*) FILTER (WHERE source_ip::text = '192.168.137.2') AS phone_as_src,
  COUNT(*) FILTER (WHERE destination_ip::text = '192.168.137.2') AS phone_as_dst
FROM flows
WHERE device_id = 'dev_002'
""")
print(cur.fetchone())

conn.close()