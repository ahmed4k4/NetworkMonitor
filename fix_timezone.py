import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("ALTER DATABASE network_control SET timezone = 'Africa/Cairo'")
        print('Timezone set to Africa/Cairo')
        conn.commit()
finally:
    conn.close()