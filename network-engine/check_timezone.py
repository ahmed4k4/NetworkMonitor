from database.connection import get_connection
import datetime

conn = get_connection()
cursor = conn.cursor()

# Check current date/time in database
cursor.execute("SELECT NOW(), CURRENT_DATE, CURRENT_TIMESTAMP")
row = cursor.fetchone()
print(f"DB NOW: {row[0]}")
print(f"DB CURRENT_DATE: {row[1]}")
print(f"DB CURRENT_TIMESTAMP: {row[2]}")

# Check traffic_samples dates
cursor.execute("SELECT MIN(sampled_at), MAX(sampled_at) FROM traffic_samples")
row = cursor.fetchone()
print(f"Traffic samples range: {row[0]} to {row[1]}")

# Check usage_daily dates
cursor.execute("SELECT MIN(day_start), MAX(day_start) FROM usage_daily")
row = cursor.fetchone()
print(f"Usage daily range: {row[0]} to {row[1]}")

# Check devices table dates
cursor.execute("SELECT MIN(last_seen), MAX(last_seen) FROM devices")
row = cursor.fetchone()
print(f"Devices last_seen range: {row[0]} to {row[1]}")

# Check what CURRENT_DATE returns vs actual data
cursor.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes
    FROM usage_daily 
    WHERE day_start = CURRENT_DATE
""")
rows = cursor.fetchall()
print(f"\nUsage_daily for CURRENT_DATE ({datetime.date.today()}):")
for r in rows:
    print(f"  {r[0]}: day_start={r[1]}, dl={r[2]}, ul={r[3]}")

# Also check yesterday
cursor.execute("""
    SELECT device_id, day_start, download_bytes, upload_bytes
    FROM usage_daily 
    WHERE day_start = CURRENT_DATE - INTERVAL '1 day'
""")
rows = cursor.fetchall()
print(f"\nUsage_daily for yesterday:")
for r in rows:
    print(f"  {r[0]}: day_start={r[1]}, dl={r[2]}, ul={r[3]}")

conn.close()