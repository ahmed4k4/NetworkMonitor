from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()
cur.execute(
    "SELECT device_id, mac_address::text, ip_address::text, hostname, vendor, state, first_seen::text, last_seen::text, total_upload, total_download FROM devices ORDER BY last_seen DESC NULLS LAST"
)
for r in cur.fetchall():
    print(r)
return_connection(c)