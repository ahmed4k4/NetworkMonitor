from database.connection import get_connection, return_connection
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM device_app_usage')
        print(f'device_app_usage: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM device_domain_usage')
        print(f'device_domain_usage: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM device_peaks')
        print(f'device_peaks: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM device_activity_timeline')
        print(f'device_activity_timeline: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM device_category_usage')
        print(f'device_category_usage: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM device_protocol_usage')
        print(f'device_protocol_usage: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM traffic_samples')
        print(f'traffic_samples: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM usage_daily')
        print(f'usage_daily: {cur.fetchone()[0]}')
finally:
    return_connection(conn)