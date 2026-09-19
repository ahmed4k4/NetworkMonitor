from database.connection import get_connection, return_connection
from config import network_config as c

print("LAN_IP=", c.lan_ip, "GW=", c.upstream_gateway, "SUBNET=", c.lan_subnet)
conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT device_id, mac_address::text, split_part(ip_address::text,'/',1),
           hostname, vendor, state, total_upload, total_download,
           first_seen, last_seen
    FROM devices
    ORDER BY last_seen DESC NULLS LAST
""")
rows = cur.fetchall()
print("device_count =", len(rows))
for r in rows:
    print(r)
return_connection(conn)