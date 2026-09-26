import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT device_id, day_start, download_bytes, upload_bytes, packets FROM usage_daily WHERE day_start = CURRENT_DATE")
        for row in cursor.fetchall():
            print(f'usage_daily TODAY: {row}')
        cursor.execute("SELECT device_id, hour_start, download_bytes, upload_bytes, packets FROM usage_hourly WHERE hour_start = date_trunc('hour', NOW())")
        for row in cursor.fetchall():
            print(f'usage_hourly NOW: {row}')
finally:
    conn.close()