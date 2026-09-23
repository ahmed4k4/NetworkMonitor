import psycopg2
conn = psycopg2.connect(host='localhost', dbname='network_monitor', user='postgres', password='postgres')
c = conn.cursor()
c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='devices' ORDER BY ordinal_position")
print("=== DEVICES COLUMNS ===")
for r in c.fetchall():
    print(r)
c.execute("SELECT COUNT(*) FROM traffic_samples")
print("samples", c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM flows")
print("flows", c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM dns_queries")
print("dns", c.fetchone()[0])
c.execute("SELECT device_id::text, upload_today, download_today, updated_at FROM devices ORDER BY last_seen DESC LIMIT 5")
print("=== DEVICE TODAY ROWS ===")
for r in c.fetchall():
    print(r)
conn.close()