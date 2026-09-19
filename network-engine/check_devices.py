from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT device_id, mac_address, ip_address, total_upload, total_download, total_packets, state, last_seen
    FROM devices
    ORDER BY device_id
""")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()