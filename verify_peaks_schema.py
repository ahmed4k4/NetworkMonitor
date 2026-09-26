import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'device_peaks'")
        for row in cursor.fetchall():
            print(f'{row[0]}: {row[1]}')
finally:
    conn.close()