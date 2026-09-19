import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        tables = [
            'device_app_usage', 'device_domain_usage', 'device_category_usage',
            'device_protocol_usage', 'sni_observations', 'dns_queries', 'flows'
        ]
        for t in tables:
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            count = cur.fetchone()[0]
            print(f'{t}: {count} rows')
        
        print('\n--- device_app_usage sample ---')
        cur.execute('SELECT device_id, application, category, confidence, total_bytes FROM device_app_usage ORDER BY hour_start DESC LIMIT 10')
        for row in cur.fetchall():
            print(row)

        print('\n--- dns_queries with response_ip populated ---')
        cur.execute('SELECT COUNT(*) FROM dns_queries WHERE response_ip IS NOT NULL')
        print('count:', cur.fetchone()[0])
finally:
    from database.connection import return_connection
    return_connection(conn)