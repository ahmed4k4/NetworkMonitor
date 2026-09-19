from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes, packets, connections
    FROM usage_daily 
    ORDER BY day_start DESC, device_id
""")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()