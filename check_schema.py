import psycopg
conn = psycopg.connect('postgresql://postgres:12345678@localhost:5432/network_control')
cur = conn.cursor()
cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'device_domain_usage\'')
print('device_domain_usage columns:')
for row in cur.fetchall():
    print(f'  {row[0]}')
cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'device_app_usage\'')
print('device_app_usage columns:')
for row in cur.fetchall():
    print(f'  {row[0]}')