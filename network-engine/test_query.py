import sys
sys.path.append("e:/NetworkMonitor/network-engine")
from database.connection import get_connection, return_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute('SELECT download_speed_bps, upload_speed_bps, sampled_at FROM traffic_samples ORDER BY sampled_at DESC LIMIT 1')
        row = cursor.fetchone()
        print('Latest sample:', row)
except Exception as e:
    print('Error:', e)
finally:
    return_connection(conn)