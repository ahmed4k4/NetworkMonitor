import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('SELECT username, password_hash FROM users')
        for row in cur.fetchall():
            print(row)
finally:
    from database.connection import return_connection
    return_connection(conn)