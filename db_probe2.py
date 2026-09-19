import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, role, is_active, LEFT(password_hash, 10) AS hash_prefix, LENGTH(password_hash) AS hash_len FROM users ORDER BY id")
        users = cur.fetchall()
        print("USERS:")
        for u in users:
            print("  ", u)
        cur.execute("SELECT COUNT(*) FROM traffic_samples")
        print("traffic_samples:", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM internet")
except Exception as e:
    import traceback; traceback.print_exc()
    conn.rollback()
finally:
    from database.connection import close_pool
    close_pool()