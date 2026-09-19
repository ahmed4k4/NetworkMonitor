import psycopg

print("=" * 80)
print("DATABASE PERSISTENCE VERIFICATION (Direct SQL)")
print("=" * 80)

conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')

# 1. Verify all historical tables have data
print("\n1. USAGE_DAILY - All devices, all days")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, day_start, download_bytes, upload_bytes, packets
        FROM usage_daily
        ORDER BY device_id, day_start;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | DL={row[2]:>12} | UL={row[3]:>12} | PKT={row[4]}")

# 2. Verify usage_hourly
print("\n2. USAGE_HOURLY - Recent entries")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, hour_start, download_bytes, upload_bytes, packets
        FROM usage_hourly
        ORDER BY hour_start DESC
        LIMIT 20;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | DL={row[2]:>12} | UL={row[3]:>12} | PKT={row[4]}")

# 3. Verify usage_monthly
print("\n3. USAGE_MONTHLY - All entries")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, month_start, download_bytes, upload_bytes, packets
        FROM usage_monthly
        ORDER BY device_id, month_start;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | DL={row[2]:>12} | UL={row[3]:>12} | PKT={row[4]}")

# 4. Verify device totals match daily aggregation
print("\n4. DEVICE TOTALS vs DAILY SUM")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT d.device_id, 
               d.total_download, d.total_upload,
               COALESCE(SUM(ud.download_bytes), 0), COALESCE(SUM(ud.upload_bytes), 0)
        FROM devices d
        LEFT JOIN usage_daily ud ON ud.device_id = d.device_id
        GROUP BY d.device_id, d.total_download, d.total_upload
        ORDER BY d.device_id;
    """)
    for row in cur.fetchall():
        dl_match = "✓" if row[1] == row[3] else "✗ MISMATCH"
        ul_match = "✓" if row[2] == row[4] else "✗ MISMATCH"
        print(f"  {row[0]}: Device DL={row[1]} vs Sum DL={row[3]} {dl_match} | Device UL={row[2]} vs Sum UL={row[4]} {ul_match}")

# 5. Verify timezone consistency
print("\n5. TIMEZONE CONSISTENCY CHECK")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("SHOW timezone;")
    tz = cur.fetchone()[0]
    cur.execute("SELECT NOW(), CURRENT_DATE, date_trunc('day', NOW())::date;")
    now, cdate, trunc = cur.fetchone()
    print(f"  DB Timezone: {tz}")
    print(f"  NOW(): {now}")
    print(f"  CURRENT_DATE: {cdate}")
    print(f"  date_trunc('day', NOW())::date: {trunc}")
    print(f"  Match: {'YES' if cdate == trunc else 'NO'}")

# 6. Check for any data integrity issues
print("\n6. DATA INTEGRITY CHECKS")
print("-" * 40)
with conn.cursor() as cur:
    # Negative values
    cur.execute("SELECT COUNT(*) FROM usage_daily WHERE download_bytes < 0 OR upload_bytes < 0;")
    neg = cur.fetchone()[0]
    print(f"  Negative values in usage_daily: {neg}")
    
    cur.execute("SELECT COUNT(*) FROM usage_hourly WHERE download_bytes < 0 OR upload_bytes < 0;")
    neg = cur.fetchone()[0]
    print(f"  Negative values in usage_hourly: {neg}")
    
    cur.execute("SELECT COUNT(*) FROM usage_monthly WHERE download_bytes < 0 OR upload_bytes < 0;")
    neg = cur.fetchone()[0]
    print(f"  Negative values in usage_monthly: {neg}")
    
    # Zero days with data (should be none for active devices)
    cur.execute("""
        SELECT device_id, day_start FROM usage_daily 
        WHERE download_bytes = 0 AND upload_bytes = 0 AND packets = 0;
    """)
    zero_days = cur.fetchall()
    print(f"  Zero-usage days: {len(zero_days)}")
    for z in zero_days[:5]:
        print(f"    {z[0]} | {z[1]}")

# 7. Verify traffic_samples hourly bucketing
print("\n7. TRAFFIC_SAMPLES HOURLY ALIGNMENT")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, 
               date_trunc('hour', sampled_at) as hour_bucket,
               COUNT(*) as sample_count,
               SUM(download_bytes) as total_dl,
               SUM(upload_bytes) as total_ul
        FROM traffic_samples
        WHERE device_id = 'dev_003'
          AND sampled_at >= NOW() - INTERVAL '24 hours'
        GROUP BY device_id, date_trunc('hour', sampled_at)
        ORDER BY hour_bucket;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | samples={row[2]} | DL={row[3]} | UL={row[4]}")

# 8. Check quota used_bytes sync with usage_daily
print("\n8. QUOTA used_bytes vs USAGE_DAILY")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT dl.device_id, 
               dl.used_bytes as quota_used,
               COALESCE(SUM(ud.download_bytes + ud.upload_bytes), 0) as daily_sum
        FROM data_limits dl
        LEFT JOIN usage_daily ud ON ud.device_id = dl.device_id
            AND ud.day_start = CURRENT_DATE
        WHERE dl.enabled = TRUE
        GROUP BY dl.device_id, dl.used_bytes
        ORDER BY dl.device_id;
    """)
    for row in cur.fetchall():
        match = "✓" if row[1] == row[2] else "✗ MISMATCH"
        print(f"  {row[0]}: Quota used={row[1]} | Daily sum={row[2]} {match}")

conn.close()

print("\n" + "=" * 80)
print("DATABASE PERSISTENCE VERIFICATION COMPLETE")
print("=" * 80)