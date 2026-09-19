from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()

print("=== DEVICES table ===")
cur.execute("""
    SELECT device_id, mac_address::text, ip_address::text, hostname, state,
           total_upload, total_download, last_seen
    FROM devices ORDER BY device_id
""")
for r in cur.fetchall():
    print(r)

print("\n=== usage_daily (last 10 rows) ===")
cur.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes
    FROM usage_daily ORDER BY day_start DESC LIMIT 10
""")
for r in cur.fetchall():
    print(r)

print("\n=== traffic_samples (last 10 rows) ===")
cur.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes,
           download_speed_bps, upload_speed_bps, packets
    FROM traffic_samples ORDER BY sampled_at DESC LIMIT 10
""")
for r in cur.fetchall():
    print(r)

print("\n=== flows summary by device ===")
cur.execute("""
    SELECT src_ip, dst_ip, direction, SUM(bytes), COUNT(*)
    FROM flows GROUP BY src_ip, dst_ip, direction ORDER BY SUM(bytes) DESC LIMIT 20
""")
for r in cur.fetchall():
    print(r)

return_connection(c)