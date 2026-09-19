from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT device_id, sampled_at, download_bytes, upload_bytes, 
           download_speed_bps, upload_speed_bps 
    FROM traffic_samples 
    ORDER BY sampled_at DESC LIMIT 20
""")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()