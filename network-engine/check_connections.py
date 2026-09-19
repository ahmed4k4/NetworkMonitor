from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT id, device_id, source_ip, destination_ip, source_port, destination_port, 
           protocol, state, started_at, last_seen, closed_at
    FROM connections
    ORDER BY last_seen DESC
    LIMIT 30
""")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()