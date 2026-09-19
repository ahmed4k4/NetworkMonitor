import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection
from datetime import datetime

conn = get_connection()
cur = conn.cursor()

print("=== DEVICES ===")
cur.execute("""
SELECT device_id, mac_address, ip_address, hostname, custom_name, vendor,
       state, first_seen, last_seen, total_upload, total_download
FROM devices
ORDER BY last_seen DESC NULLS LAST
""")
rows = cur.fetchall()
for r in rows:
    print(r)

print()
print("=== NOW (DB) ===")
cur.execute("SELECT NOW()")
print(cur.fetchone()[0])

print()
print("=== TRAFFIC SAMPLES (latest per device) ===")
cur.execute("""
SELECT device_id, COUNT(*), MAX(sampled_at), MIN(sampled_at)
FROM traffic_samples
GROUP BY device_id
ORDER BY MAX(sampled_at) DESC NULLS LAST
""")
for r in cur.fetchall():
    print(r)

print()
print("=== FLOWS (latest per device) ===")
cur.execute("""
SELECT device_id, COUNT(*), MAX(last_seen)
FROM flows
GROUP BY device_id
ORDER BY MAX(last_seen) DESC NULLS LAST
""")
for r in cur.fetchall():
    print(r)

conn.close()