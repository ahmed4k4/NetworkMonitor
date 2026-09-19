import psycopg

conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute('SELECT device_id, used_bytes, daily_quota_bytes, weekly_quota_bytes, monthly_quota_bytes, reset_period, enabled FROM data_limits;')
    print('data_limits:')
    for row in cur.fetchall():
        print(f'  {row}')
conn.close()