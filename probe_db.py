import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute('SELECT device_id, sampled_at, download_bytes, upload_bytes, packets, download_speed_bps, upload_speed_bps FROM traffic_samples ORDER BY sampled_at DESC LIMIT 10')
        for row in cursor.fetchall():
            print(f'traffic_samples: {row}')
        cursor.execute('SELECT device_id, direction, packets, bytes, upload_bytes, download_bytes, state FROM flows ORDER BY last_seen DESC LIMIT 10')
        for row in cursor.fetchall():
            print(f'flows: {row}')
        cursor.execute("SELECT device_id, mac_address::text, split_part(ip_address::text, '/', 1), state, total_upload, total_download, total_packets FROM devices ORDER BY last_seen DESC")
        for row in cursor.fetchall():
            print(f'devices: {row}')
finally:
    conn.close()