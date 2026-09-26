import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        # Check usage_daily with Africa/Cairo timezone - TODAY
        cursor.execute("SELECT device_id, day_start, download_bytes, upload_bytes, packets FROM usage_daily WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date")
        rows = cursor.fetchall()
        print(f'usage_daily TODAY (Cairo) rows: {len(rows)}')
        for row in rows:
            print(f'  {row}')
        # Check what dates exist
        cursor.execute("SELECT DISTINCT day_start FROM usage_daily ORDER BY day_start DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f'  Existing day_start: {row}')
finally:
    conn.close()