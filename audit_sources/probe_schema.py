import psycopg

c = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control',
                    user='network_admin', password='12345678')
cur = c.cursor()
rows = ['traffic_samples', 'usage_daily', 'usage_hourly', 'usage_monthly',
        'device_app_usage', 'device_domain_usage', 'device_protocol_usage',
        'device_category_usage', 'device_peaks', 'device_activity_timeline', 'devices']
for t in rows:
    print('=== ' + t + ' ===')
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name=%s ORDER BY ordinal_position", (t,))
    for r in cur.fetchall():
        print(r)
c.close()