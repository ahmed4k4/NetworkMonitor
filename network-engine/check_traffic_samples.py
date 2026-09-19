import psycopg
conn = psycopg.connect('postgresql://postgres:12345678@localhost:5432/network_control')
cur = conn.cursor()

# Check usage_daily for dev_001
cur.execute("SELECT * FROM usage_daily WHERE device_id = 'dev_001' ORDER BY day_start DESC LIMIT 10")
rows = cur.fetchall()
col_names = [desc[0] for desc in cur.description]
print("usage_daily columns:", col_names)
for row in rows:
    print(row)

print("\n---")

# Check traffic_samples sum
cur.execute("SELECT device_id, SUM(download_bytes) as total_dl, SUM(upload_bytes) as total_ul FROM traffic_samples GROUP BY device_id ORDER BY (SUM(download_bytes) + SUM(upload_bytes)) DESC LIMIT 10")
rows = cur.fetchall()
for row in rows:
    print(f"Device {row[0]}: DL={row[1]}, UL={row[2]}, Total={row[1]+row[2]}")

print("\n---")

# Check recent traffic_samples for dev_001
cur.execute("SELECT * FROM traffic_samples WHERE device_id = 'dev_001' ORDER BY sampled_at DESC LIMIT 10")
rows = cur.fetchall()
col_names = [desc[0] for desc in cur.description]
for row in rows:
    print(row)

print("\n---")

# Check device totals from devices table
cur.execute("SELECT device_id, total_download, total_upload, total_packets FROM devices WHERE device_id = 'dev_001'")
rows = cur.fetchall()
col_names = [desc[0] for desc in cur.description]
print("devices total:", col_names)
for row in rows:
    print(row)

conn.close()