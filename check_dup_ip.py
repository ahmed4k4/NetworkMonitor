import psycopg
conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute('''
        SELECT device_id, mac_address::text, split_part(ip_address::text, '/', 1) as ip, hostname, vendor, state
        FROM devices
        WHERE split_part(ip_address::text, '/', 1) = '192.168.137.100';
    ''')
    for row in cur.fetchall():
        hostname = row[3] or "NULL"
        vendor = row[4] or "NULL"
        print(f'{row[0]:<20} {row[1]:<20} {row[2]:<18} {hostname:<20} {vendor:<20} {row[5]}')
conn.close()