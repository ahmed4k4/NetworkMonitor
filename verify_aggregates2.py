import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT device_id, peak_type, peak_value, recorded_at FROM device_peaks ORDER BY recorded_at DESC LIMIT 10")
        for row in cursor.fetchall():
            print(f'device_peaks: {row}')
finally:
    conn.close()