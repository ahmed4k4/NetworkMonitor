from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

print("=== ISSUE 1: Device Details Upload summary ===")
# Check dev_001 - has upload in usage_daily but devices.total_upload=158122
cursor.execute("""
    SELECT device_id, total_upload, total_download 
    FROM devices 
    WHERE device_id = 'dev_001'
""")
row = cursor.fetchone()
print(f"dev_001 devices table: total_upload={row[1]}, total_download={row[2]}")

cursor.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes
    FROM usage_daily 
    WHERE device_id = 'dev_001' AND day_start = CURRENT_DATE
""")
row = cursor.fetchone()
print(f"dev_001 usage_daily today: download={row[2]}, upload={row[3]}")

print("\n=== ISSUE 2: Traffic History shows non-zero upload ===")
cursor.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes, download_speed_bps, upload_speed_bps
    FROM traffic_samples 
    WHERE device_id = 'dev_001'
    ORDER BY sampled_at DESC LIMIT 5
""")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[1]}: dl_bytes={r[2]}, ul_bytes={r[3]}, dl_bps={r[4]}, ul_bps={r[5]}")

print("\n=== ISSUE 3: Devices list Download Today = 0 ===")
cursor.execute("""
    SELECT device_id, total_download, 
           COALESCE((SELECT download_bytes FROM usage_daily ud WHERE ud.device_id = d.device_id AND ud.day_start = CURRENT_DATE), 0) as download_today
    FROM devices d
    WHERE device_id IN ('dev_001', 'dev_002', 'dev_003')
""")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: total_download={r[1]}, download_today={r[2]}")

print("\n=== ISSUE 4: Device Details Current Speed ===")
# Check latest traffic sample for each device
cursor.execute("""
    SELECT DISTINCT ON (device_id) device_id, sampled_at, download_speed_bps, upload_speed_bps
    FROM traffic_samples 
    WHERE device_id IN ('dev_001', 'dev_002', 'dev_003', 'test_dev_pipeline')
    ORDER BY device_id, sampled_at DESC
""")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: sampled_at={r[1]}, dl_bps={r[2]}, ul_bps={r[3]}, current={r[2]+r[3]}")

print("\n=== ISSUE 5: Active Connections implausibly large ===")
cursor.execute("SELECT COUNT(*) FROM flows WHERE state = 'ACTIVE'")
print(f"Active flows: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM connections WHERE state = 'ACTIVE'")
print(f"Active connections: {cursor.fetchone()[0]}")

# Check how many flows are actually old
cursor.execute("""
    SELECT COUNT(*) FROM flows 
    WHERE state = 'ACTIVE' AND last_seen < NOW() - INTERVAL '5 minutes'
""")
print(f"Active flows older than 5 min: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) FROM flows 
    WHERE state = 'ACTIVE' AND last_seen < NOW() - INTERVAL '1 hour'
""")
print(f"Active flows older than 1 hour: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) FROM flows 
    WHERE state = 'ACTIVE' AND last_seen < NOW() - INTERVAL '1 day'
""")
print(f"Active flows older than 1 day: {cursor.fetchone()[0]}")

# Check flow_timeout config
cursor.execute("SELECT * FROM settings WHERE key = 'flow_timeout'")
row = cursor.fetchone()
print(f"flow_timeout setting: {row}")

conn.close()