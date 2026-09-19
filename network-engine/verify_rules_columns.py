import psycopg

conn = psycopg.connect("host=127.0.0.1 port=5432 dbname=network_control user=postgres password=12345678")
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='network_rules' ORDER BY ordinal_position")
print("=== network_rules columns ===")
for r in cur.fetchall():
    print(r)

# Check devices table key columns used in join
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='devices' AND column_name IN ('device_id','custom_name','hostname','ip_address') ORDER BY ordinal_position")
print("=== devices columns (join) ===")
for r in cur.fetchall():
    print(r)
conn.close()