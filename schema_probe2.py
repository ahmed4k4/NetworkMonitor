#!/usr/bin/env python3
"""Dump live PostgreSQL schema + data snapshots (per-table error isolation)."""
import json
import psycopg

CONN = "host=127.0.0.1 port=5432 dbname=network_control user=postgres password=12345678"

conn = psycopg.connect(CONN)
cur = conn.cursor()

tables = ["alerts","applications","audit_logs","connections","data_limits",
    "device_activity_timeline","device_app_usage","device_category_usage",
    "device_domain_usage","device_peaks","device_protocol_usage","devices",
    "dns_queries","domains","events","firewall_rules","flows","interfaces",
    "network_rules","protocols","settings","sni_observations","speed_limits",
    "traffic_samples","usage_daily","usage_hourly","usage_monthly","users"]

print("=== ROW COUNTS ===")
for t in tables:
    try:
        conn.rollback()
        cur.execute(f'SELECT count(*) FROM "{t}"')
        print(f"  {t}: {cur.fetchone()[0]}")
    except Exception as e:
        conn.rollback()
        print(f"  {t}: ERR {type(e).__name__} {e}")

conn.rollback()
print("\n=== DEVICES ===")
cur.execute("""
    SELECT device_id, mac_address, ip_address, hostname, vendor, state,
           first_seen, last_seen, total_upload, total_download, total_packets, custom_name
    FROM devices ORDER BY last_seen DESC NULLS LAST
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== TRAFFIC SAMPLES (latest 20) ===")
cur.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes, packets, connections,
           download_speed_bps, upload_speed_bps
    FROM traffic_samples ORDER BY sampled_at DESC LIMIT 20
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== USAGE_DAILY (latest 10) ===")
cur.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes, packets, connections
    FROM usage_daily ORDER BY day_start DESC LIMIT 10
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== USAGE_HOURLY (latest 10) ===")
cur.execute("""
    SELECT device_id, hour_start, download_bytes, upload_bytes, packets, connections
    FROM usage_hourly ORDER BY hour_start DESC LIMIT 10
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== FLOWS (latest 10) ===")
cur.execute("""
    SELECT device_id, source_ip, destination_ip, destination_port, protocol,
           direction, started_at, last_seen, packets, bytes, upload_bytes, download_bytes, state
    FROM flows ORDER BY last_seen DESC NULLS LAST LIMIT 10
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== DEVICE_DOMAIN_USAGE (latest 15) ===")
cur.execute("""
    SELECT device_id, domain, hour_start, download_bytes, upload_bytes, queries, connections, confidence
    FROM device_domain_usage ORDER BY hour_start DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== DEVICE_APP_USAGE (latest 15) ===")
cur.execute("""
    SELECT device_id, application, category, confidence, hour_start, download_bytes, upload_bytes, connections
    FROM device_app_usage ORDER BY hour_start DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== DEVICE_PROTOCOL_USAGE (latest 15) ===")
cur.execute("""
    SELECT device_id, protocol, hour_start, download_bytes, upload_bytes, packets, connections
    FROM device_protocol_usage ORDER BY hour_start DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== DEVICE_CATEGORY_USAGE (latest 15) ===")
cur.execute("""
    SELECT device_id, category, hour_start, download_bytes, upload_bytes, connections
    FROM device_category_usage ORDER BY hour_start DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== DEVICE_PEAKS ===")
cur.execute("""
    SELECT device_id, peak_type, peak_value, peak_at, day, hour
    FROM device_peaks ORDER BY peak_at DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

print("\n=== DEVICE_ACTIVITY_TIMELINE (latest 15) ===")
cur.execute("""
    SELECT device_id, hour_start, is_active, total_bytes, connections
    FROM device_activity_timeline ORDER BY hour_start DESC LIMIT 15
""")
for r in cur.fetchall():
    print("  ", json.dumps(r, default=str))

cur.close()
conn.close()