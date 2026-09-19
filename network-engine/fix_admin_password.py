import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
import bcrypt
from database.connection import get_connection

# Generate correct hash for "admin"
new_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt())
print(f'New hash for "admin": {new_hash}')

# Update database
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('UPDATE users SET password_hash = %s WHERE username = %s', (new_hash.decode('utf-8'), 'admin'))
        conn.commit()
        print(f'Updated {cur.rowcount} row(s)')
finally:
    from database.connection import return_connection
    return_connection(conn)