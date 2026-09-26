import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM usage_hourly WHERE hour_start >= (NOW() - INTERVAL '1 hour') ORDER BY hour_start DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f'usage_hourly: {row}')
        
        cursor.execute("SELECT * FROM usage_monthly ORDER BY month_start DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f'usage_monthly: {row}')
        
        cursor.execute("SELECT device_id, peak_type, peak_value, peak_timestamp FROM device_peaks ORDER BY peak_timestamp DESC LIMIT 10")
        for row in cursor.fetchall():
            print(f'device_peaks: {row}')
finally:
    conn.close()