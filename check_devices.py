import psycopg
conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    cur.execute('''
        SELECT device_id, mac_address::text, split_part(ip_address::text, '/', 1) as ip, hostname, vendor, state, first_seen, last_seen
        FROM devices
        ORDER BY device_id;
    ''')
    for row in cur.fetchall():
        hostname = row[3] or "NULL"
        vendor = row[4] or "NULL"
        print(f'{row[0]:<20} {row[1]:<20} {row[2]:<18} {hostname:<30} {vendor:<20} {row[5]:<10} {row[6]} -> {row[7]}')
conn.close()