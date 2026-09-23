import psycopg2

conn = psycopg2.connect(host="localhost", dbname="network_control", user="postgres", password="12345678")
cur = conn.cursor()

cur.execute(
    """
    UPDATE devices d
    SET total_download = f.down,
        total_upload   = f.up,
        total_packets  = f.pkts
    FROM (
        SELECT device_id,
               coalesce(sum(download_bytes),0)::bigint AS down,
               coalesce(sum(upload_bytes),0)::bigint   AS up,
               coalesce(sum(packets),0)::bigint        AS pkts
        FROM flows
        GROUP BY device_id
    ) f
    WHERE d.device_id = f.device_id
    """
)
print("devices updated:", cur.rowcount)
conn.commit()

cur.execute("SELECT device_id, total_download, total_upload, total_packets FROM devices ORDER BY device_id")
for r in cur.fetchall():
    print(r)
cur.close()
conn.close()