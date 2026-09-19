import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1", port=5432, dbname="network_control",
    user="postgres", password="12345678",
)
conn.autocommit = True
cur = conn.cursor()

print("=== tables ===")
cur.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='public' ORDER BY table_name"
)
for r in cur.fetchall():
    print("  ", r[0])

print("\n=== counts ===")
for table in ("devices", "traffic_samples", "usage_daily", "usage_hourly", "usage_monthly", "flows"):
    try:
        cur.execute(f"SELECT count(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"  {table}: ERROR {e}")

print("\n=== latest traffic_samples ===")
cur.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes,
           download_speed_bps, upload_speed_bps, packets, connections
    FROM traffic_samples ORDER BY sampled_at DESC LIMIT 8
""")
for r in cur.fetchall():
    print("  ", r)

print("\n=== devices recently active ===")
cur.execute("""
    SELECT device_id, mac_address, ip_address, hostname, state,
           first_seen, last_seen, total_upload, total_download
    FROM devices ORDER BY last_seen DESC NULLS LAST LIMIT 10
""")
for r in cur.fetchall():
    print("  ", r)

print("\n=== today usage_daily ===")
cur.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes
    FROM usage_daily WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date
    ORDER BY download_bytes DESC LIMIT 10
""")
for r in cur.fetchall():
    print("  ", r)

print("\n=== server timezone / now ===")
cur.execute("SHOW timezone")
print("  tz:", cur.fetchone()[0])
cur.execute("SELECT NOW(), (NOW() AT TIME ZONE 'Africa/Cairo')::date")
print("  now/cairo_date:", cur.fetchone())

conn.close()