#!/usr/bin/env python3
"""Dump live PostgreSQL schema + key data snapshots for the audit."""
import json
import psycopg

CONN = "host=127.0.0.1 port=5432 dbname=network_control user=postgres password=12345678"

conn = psycopg.connect(CONN)
cur = conn.cursor()

# 1. List all tables
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]
print("=== TABLES ===")
print(json.dumps(tables, indent=2))

# 2. Columns for key tables
KEY = ["devices", "flows", "traffic_samples", "connections", "dns_queries",
       "sni_observations", "device_app_usage", "device_domain_usage",
       "device_category_usage", "device_protocol_usage", "usage_hourly",
       "usage_daily", "usage_monthly", "device_peaks", "device_activity_timeline"]

for t in tables:
    if t in KEY:
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            ORDER BY ordinal_position
        """, (t,))
        cols = cur.fetchall()
        print(f"\n=== COLUMNS: {t} ===")
        for c in cols:
            print(f"  {c[0]:30s} {c[1]:20s} null={c[2]:3s} default={c[3]}")

# 3. Row counts
print("\n=== ROW COUNTS ===")
for t in tables:
    try:
        cur.execute(f'SELECT count(*) FROM "{t}"')
        print(f"  {t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"  {t}: ERR {e}")

# 4. Device rows (identity fields + status)
print("\n=== DEVICES ===")
cur.execute("""
    SELECT device_id, mac_address, ip_address, hostname, state, first_seen, last_seen,
           total_download, total_upload, total_connections, total_packets
    FROM devices ORDER BY last_seen DESC NULLS LAST
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

# 5. Latest traffic samples
print("\n=== TRAFFIC SAMPLES (latest 15) ===")
cur.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes,
           download_speed_bps, upload_speed_bps, packet_count, connection_count
    FROM traffic_samples ORDER BY sampled_at DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

# 6. usage_daily latest
print("\n=== USAGE_DAILY (latest 10) ===")
cur.execute("""
    SELECT device_id, day_start, total_download, total_upload
    FROM usage_daily ORDER BY day_start DESC LIMIT 10
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

cur.close()
conn.close()