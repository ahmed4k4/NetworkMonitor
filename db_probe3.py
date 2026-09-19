import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
import bcrypt
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT username, password_hash, is_active FROM users")
        for username, phash, active in cur.fetchall():
            print(f"\nUSER {username} (active={active})")
            for pwd in ["admin", "admin_change_me", "admin123", "password", "12345678"]:
                try:
                    ok = bcrypt.checkpw(pwd.encode('utf-8'), phash.encode('utf-8'))
                    print(f"   password '{pwd}': {ok}")
                except Exception as e:
                    print(f"   password '{pwd}': ERROR {e}")
except Exception as e:
    import traceback; traceback.print_exc()
    conn.rollback()
finally:
    from database.connection import close_pool
    close_pool()