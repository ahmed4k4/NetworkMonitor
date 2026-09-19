import psycopg
import requests
import json
from datetime import datetime, timezone, timedelta

print("=" * 80)
print("COMPREHENSIVE HISTORICAL ANALYTICS AUDIT")
print("=" * 80)

# 1. DATABASE TIMEZONE CHECK
print("\n1. DATABASE TIMEZONE CHECK")
print("-" * 40)
conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute('SHOW timezone;')
    db_tz = cur.fetchone()[0]
    cur.execute('SELECT NOW();')
    db_now = cur.fetchone()[0]
    cur.execute('SELECT CURRENT_DATE;')
    db_date = cur.fetchone()[0]
    cur.execute("SELECT date_trunc('day', NOW())::date;")
    db_trunc = cur.fetchone()[0]
    
print(f"  DB Timezone: {db_tz}")
print(f"  DB NOW(): {db_now}")
print(f"  DB CURRENT_DATE: {db_date}")
print(f"  DB date_trunc('day', NOW()): {db_trunc}")
print(f"  Python NOW (local): {datetime.now()}")
print(f"  Python NOW (UTC): {datetime.now(timezone.utc)}")

# 2. CHECK FOR DUPLICATE RECORDS IN USAGE TABLES
print("\n2. DUPLICATE RECORD CHECK")
print("-" * 40)
with conn.cursor() as cur:
    # usage_daily duplicates
    cur.execute("""
        SELECT device_id, day_start, COUNT(*) as cnt
        FROM usage_daily
        GROUP BY device_id, day_start
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC;
    """)
    dupes_daily = cur.fetchall()
    print(f"  usage_daily duplicates: {len(dupes_daily)}")
    for d in dupes_daily[:5]:
        print(f"    {d}")
    
    # usage_hourly duplicates
    cur.execute("""
        SELECT device_id, hour_start, COUNT(*) as cnt
        FROM usage_hourly
        GROUP BY device_id, hour_start
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC;
    """)
    dupes_hourly = cur.fetchall()
    print(f"  usage_hourly duplicates: {len(dupes_hourly)}")
    for d in dupes_hourly[:5]:
        print(f"    {d}")
    
    # usage_monthly duplicates
    cur.execute("""
        SELECT device_id, month_start, COUNT(*) as cnt
        FROM usage_monthly
        GROUP BY device_id, month_start
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC;
    """)
    dupes_monthly = cur.fetchall()
    print(f"  usage_monthly duplicates: {len(dupes_monthly)}")
    for d in dupes_monthly[:5]:
        print(f"    {d}")

# 3. CHECK FOR MISSING DAYS (GAPS)
print("\n3. GAP ANALYSIS (missing days)")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, 
               MIN(day_start) as first_day,
               MAX(day_start) as last_day,
               COUNT(*) as days_with_data,
               (MAX(day_start) - MIN(day_start)) + 1 as expected_days
        FROM usage_daily
        GROUP BY device_id
        ORDER BY device_id;
    """)
    gaps = cur.fetchall()
    for g in gaps:
        missing = g[4] - g[3]
        if missing > 0:
            print(f"  {g[0]}: {g[3]} days of data, {g[4]} expected, {missing} missing days (range: {g[1]} to {g[2]})")

# 4. COMPARE DEVICE TOTALS vs USAGE_DAILY AGGREGATION
print("\n4. DEVICE TOTALS vs USAGE_DAILY AGGREGATION")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT d.device_id, 
               d.total_download as device_total_dl,
               d.total_upload as device_total_ul,
               COALESCE(SUM(ud.download_bytes), 0) as daily_sum_dl,
               COALESCE(SUM(ud.upload_bytes), 0) as daily_sum_ul
        FROM devices d
        LEFT JOIN usage_daily ud ON ud.device_id = d.device_id
        GROUP BY d.device_id, d.total_download, d.total_upload
        ORDER BY d.device_id;
    """)
    totals = cur.fetchall()
    for t in totals:
        dl_match = "✓" if t[1] == t[3] else "✗"
        ul_match = "✓" if t[2] == t[4] else "✗"
        print(f"  {t[0]}: Device DL={t[1]}, Daily Sum DL={t[3]} {dl_match} | Device UL={t[2]}, Daily Sum UL={t[4]} {ul_match}")

# 5. VERIFY MONTHLY AGGREGATION IS CORRECT
print("\n5. MONTHLY AGGREGATION VERIFICATION")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, month_start, download_bytes, upload_bytes
        FROM usage_monthly
        ORDER BY device_id, month_start;
    """)
    monthly = cur.fetchall()
    for m in monthly:
        print(f"  {m[0]}: {m[1]} DL={m[2]}, UL={m[3]}")
    
    # Cross-check with daily for August 2026
    cur.execute("""
        SELECT device_id, 
               SUM(download_bytes) as sum_dl,
               SUM(upload_bytes) as sum_ul
        FROM usage_daily
        WHERE day_start >= '2026-08-01' AND day_start < '2026-09-01'
        GROUP BY device_id;
    """)
    aug_daily = cur.fetchall()
    print("\n  August 2026 from daily:")
    for a in aug_daily:
        print(f"    {a[0]}: DL={a[1]}, UL={a[2]}")

# 6. VERIFY WEEKLY AGGREGATION (should be 7-day periods)
print("\n6. WEEKLY AGGREGATION CHECK")
print("-" * 40)
with conn.cursor() as cur:
    # The weekly endpoint currently queries usage_daily, not a weekly table
    # Check if there's a weekly table
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name LIKE '%weekly%';
    """)
    weekly_tables = cur.fetchall()
    print(f"  Weekly tables: {weekly_tables}")
    
    # Current weekly endpoint logic: last 7 days from usage_daily
    cur.execute("""
        SELECT day_start, download_bytes, upload_bytes
        FROM usage_daily
        WHERE device_id = 'dev_003'
          AND day_start >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY day_start;
    """)
    week_data = cur.fetchall()
    print("  Last 7 days for dev_003:")
    total_dl = 0
    total_ul = 0
    for w in week_data:
        print(f"    {w[0]}: DL={w[1]}, UL={w[2]}")
        total_dl += w[1]
        total_ul += w[2]
    print(f"    TOTAL: DL={total_dl}, UL={total_ul}")

# 7. CHECK TRAFFIC_SAMPLES FOR HOURLY BOUNDARY ALIGNMENT
print("\n7. TRAFFIC_SAMPLES HOURLY BOUNDARY CHECK")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("""
        SELECT device_id, sampled_at, download_bytes, upload_bytes
        FROM traffic_samples
        WHERE device_id = 'dev_003'
        ORDER BY sampled_at DESC
        LIMIT 20;
    """)
    samples = cur.fetchall()
    for s in samples:
        minute = s[1].minute
        second = s[1].second
        print(f"  {s[0]}: {s[1]} (min={minute}, sec={second}) DL={s[2]}, UL={s[3]}")

# 8. VERIFY API RESPONSES MATCH SQL
print("\n8. API vs SQL VERIFICATION")
print("-" * 40)
base_url = "http://127.0.0.1:8000"
login_resp = requests.post(f"{base_url}/api/auth/login", json={"username": "admin", "password": "admin_change_me"})
token = login_resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Test daily
resp = requests.get(f"{base_url}/api/analytics/daily?device_id=dev_003", headers=headers)
api_daily = resp.json()
print("  API /analytics/daily?device_id=dev_003:")
for a in api_daily:
    print(f"    {a['time']}: DL={a['download']}, UL={a['upload']}")

# SQL for same
with conn.cursor() as cur:
    cur.execute("""
        SELECT day_start::text, download_bytes, upload_bytes
        FROM usage_daily
        WHERE device_id = 'dev_003'
        ORDER BY day_start DESC;
    """)
    sql_daily = cur.fetchall()
print("  SQL usage_daily for dev_003:")
for s in sql_daily:
    print(f"    {s[0]}: DL={s[1]}, UL={s[2]}")

# 9. CHECK CURRENT_DATE BOUNDARY ISSUES
print("\n9. DATE BOUNDARY CHECK (CURRENT_DATE vs actual)")
print("-" * 40)
with conn.cursor() as cur:
    cur.execute("SELECT NOW() AT TIME ZONE 'GMT', NOW() AT TIME ZONE 'Africa/Cairo';")
    tz_check = cur.fetchone()
    print(f"  NOW() in GMT: {tz_check[0]}")
    print(f"  NOW() in Cairo: {tz_check[1]}")
    cur.execute("SELECT CURRENT_DATE, (NOW() AT TIME ZONE 'Africa/Cairo')::date;")
    date_check = cur.fetchone()
    print(f"  CURRENT_DATE (DB): {date_check[0]}")
    print(f"  Date in Cairo: {date_check[1]}")

# 10. TEST CUSTOM RANGE ENDPOINTS (device intelligence)
print("\n10. DEVICE INTELLIGENCE ENDPOINTS (custom ranges)")
print("-" * 40)
endpoints = [
    ("/api/devices/dev_003/intelligence?range=24h", "24h"),
    ("/api/devices/dev_003/intelligence?range=7d", "7d"),
    ("/api/devices/dev_003/intelligence?range=30d", "30d"),
    ("/api/devices/dev_003/applications?range=24h", "apps 24h"),
    ("/api/devices/dev_003/domains?range=24h", "domains 24h"),
    ("/api/devices/dev_003/categories?range=24h", "categories 24h"),
    ("/api/devices/dev_003/protocols?range=24h", "protocols 24h"),
]
for ep, name in endpoints:
    resp = requests.get(f"{base_url}{ep}", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            print(f"  {name}: {len(data)} items")
        elif isinstance(data, dict):
            print(f"  {name}: {list(data.keys())}")
    else:
        print(f"  {name}: ERROR {resp.status_code} - {resp.text[:100]}")

conn.close()
print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)