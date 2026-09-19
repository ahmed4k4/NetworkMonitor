import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection
from datetime import datetime, timedelta

c = get_connection()
cur = c.cursor()

print("=" * 80)
print("REAL DATA PIPELINE VERIFICATION (engine running with fixes)")
print("=" * 80)

# 1. devices
print("\n=== devices (last_seen within 10 min) ===")
cur.execute("""
    SELECT device_id, mac_address, ip_address, hostname, state,
           first_seen, last_seen, total_upload, total_download, total_packets
    FROM devices
    WHERE last_seen > NOW() - INTERVAL '10 minutes'
    ORDER BY last_seen DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} mac={row[1]} ip={row[2]} state={row[4]} last_seen={row[6]} up={row[7]} down={row[8]} pkts={row[9]}")

# 2. traffic_samples
print("\n=== traffic_samples (last 10 min, count + latest) ===")
cur.execute("""
    SELECT COUNT(*), MAX(sampled_at)
    FROM traffic_samples
    WHERE sampled_at > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes, packets,
           connections, download_speed_bps, upload_speed_bps
    FROM traffic_samples
    WHERE sampled_at > NOW() - INTERVAL '10 minutes'
    ORDER BY sampled_at DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} at={row[1]} dl={row[2]} ul={row[3]} pkts={row[4]} conns={row[5]} dl_speed={row[6]} ul_speed={row[7]}")

# 3. flows
print("\n=== flows (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(last_seen)
    FROM flows
    WHERE last_seen > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, source_ip, destination_ip, protocol, state,
           upload_bytes, download_bytes, packets
    FROM flows
    WHERE last_seen > NOW() - INTERVAL '10 minutes'
    ORDER BY last_seen DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} {row[1]}->{row[2]} proto={row[3]} state={row[4]} up={row[5]} down={row[6]} pkts={row[7]}")

# 4. dns_queries
print("\n=== dns_queries (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(queried_at)
    FROM dns_queries
    WHERE queried_at > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, domain, query_type, response_ip, queried_at
    FROM dns_queries
    WHERE queried_at > NOW() - INTERVAL '10 minutes'
    ORDER BY queried_at DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} domain={row[1]} type={row[2]} resp={row[3]} at={row[4]}")

# 5. device_app_usage
print("\n=== device_app_usage (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(hour_start)
    FROM device_app_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, application, category, confidence, hour_start,
           download_bytes, upload_bytes, connections
    FROM device_app_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
    ORDER BY hour_start DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} app={row[1]} cat={row[2]} conf={row[3]} at={row[4]} dl={row[5]} ul={row[6]} conns={row[7]}")

# 6. device_domain_usage
print("\n=== device_domain_usage (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(hour_start)
    FROM device_domain_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, domain, category, confidence, hour_start,
           download_bytes, upload_bytes, queries, connections
    FROM device_domain_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
    ORDER BY hour_start DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} domain={row[1]} cat={row[2]} conf={row[3]} at={row[4]} dl={row[5]} ul={row[6]} q={row[7]} conns={row[8]}")

# 7. device_category_usage
print("\n=== device_category_usage (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(hour_start)
    FROM device_category_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, category, hour_start, download_bytes, upload_bytes, connections
    FROM device_category_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
    ORDER BY hour_start DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} cat={row[1]} at={row[2]} dl={row[3]} ul={row[4]} conns={row[5]}")

# 8. device_protocol_usage
print("\n=== device_protocol_usage (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(hour_start)
    FROM device_protocol_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, protocol, hour_start, download_bytes, upload_bytes, packets, connections
    FROM device_protocol_usage
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
    ORDER BY hour_start DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} proto={row[1]} at={row[2]} dl={row[3]} ul={row[4]} pkts={row[5]} conns={row[6]}")

# 9. device_activity_timeline
print("\n=== device_activity_timeline (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(hour_start)
    FROM device_activity_timeline
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, hour_start, is_active, total_bytes, connections
    FROM device_activity_timeline
    WHERE hour_start > NOW() - INTERVAL '10 minutes'
    ORDER BY hour_start DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} at={row[1]} active={row[2]} bytes={row[3]} conns={row[4]}")

# 10. device_peaks
print("\n=== device_peaks (last 10 min) ===")
cur.execute("""
    SELECT COUNT(*), MAX(peak_at)
    FROM device_peaks
    WHERE peak_at > NOW() - INTERVAL '10 minutes'
""")
row = cur.fetchone()
print(f"  count={row[0]} latest={row[1]}")
cur.execute("""
    SELECT device_id, peak_type, peak_value, peak_at, day, hour
    FROM device_peaks
    WHERE peak_at > NOW() - INTERVAL '10 minutes'
    ORDER BY peak_at DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} type={row[1]} value={row[2]} at={row[3]} day={row[4]} hour={row[5]}")

# 11. usage_daily (today)
print("\n=== usage_daily (today) ===")
cur.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes, packets
    FROM usage_daily
    WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date
    ORDER BY download_bytes DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:12} day={row[1]} dl={row[2]} ul={row[3]} pkts={row[4]}")

return_connection(c)