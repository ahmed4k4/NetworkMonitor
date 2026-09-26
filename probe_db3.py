import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        # Check usage_daily with Africa/Cairo timezone (application timezone)
        cursor.execute("SELECT device_id, day_start, download_bytes, upload_bytes, packets FROM usage_daily WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date")
        for row in cursor.fetchall():
            print(f'usage_daily TODAY (Cairo): {row}')
        # Check usage_hourly with Africa/Cairo timezone
        cursor.execute("SELECT device_id, hour_start, download_bytes, upload_bytes, packets FROM usage_hourly WHERE hour_start = date_trunc('hour', NOW() AT TIME ZONE 'Africa/Cairo')")
        for row in cursor.fetchall():
            print(f'usage_hourly NOW (Cairo): {row}')
        # Also check the timezone of the DB
        cursor.execute("SHOW timezone")
        print(f'DB timezone: {cursor.fetchone()}')
finally:
    conn.close()