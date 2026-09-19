import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        for t in ['device_domain_usage', 'device_app_usage', 'device_category_usage', 'device_protocol_usage']:
            print(f'\n--- {t} columns ---')
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (t,))
            for row in cur.fetchall():
                print(' ', row)
finally:
    from database.connection import return_connection
    return_connection(conn)