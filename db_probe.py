import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
import os
from database.connection import get_connection

print("DB config:", os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_USER"))
try:
    conn = get_connection()
    print("Connected to DB successfully")
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
        tables = [r[0] for r in cur.fetchall()]
        print("TABLES:", tables)
        for t in tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                print(f"  {t}: {cur.fetchone()[0]}")
            except Exception as e:
                print(f"  {t}: ERR {e}")
    conn.rollback()
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    from database.connection import close_pool
    close_pool()