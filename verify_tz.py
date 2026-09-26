import sys
sys.path.insert(0, 'network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SHOW timezone")
        print(f'DB timezone: {cursor.fetchone()}')
        cursor.execute("SELECT (NOW() AT TIME ZONE 'Africa/Cairo')::date as cairo_today")
        print(f'Cairo today: {cursor.fetchone()}')
        cursor.execute("SELECT CURRENT_DATE as db_today")
        print(f'DB today: {cursor.fetchone()}')
finally:
    conn.close()