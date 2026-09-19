import psycopg

conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute('SHOW timezone;')
    print('Timezone:', cur.fetchone())
    cur.execute('SELECT NOW();')
    print('NOW():', cur.fetchone())
    cur.execute('SELECT CURRENT_DATE;')
    print('CURRENT_DATE:', cur.fetchone())
    cur.execute("SELECT date_trunc('day', NOW());")
    print('date_trunc day:', cur.fetchone())
conn.close()