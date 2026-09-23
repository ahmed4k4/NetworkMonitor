import psycopg2

conn = psycopg2.connect(host="localhost", dbname="network_control", user="postgres", password="12345678")
cur = conn.cursor()

cur.execute(
    """
    SELECT d.device_id, d.total_upload, d.total_download, d.total_packets,
           coalesce(f.f_count,0) AS flow_count,
           coalesce(f.f_down,0) AS flow_down,
           coalesce(f.f_up,0)  AS flow_up,
           coalesce(f.f_pkts,0) AS flow_pkts,
           coalesce(t.s_down,0) AS sam_down,
           coalesce(t.s_up,0)   AS sam_up
    FROM devices d
    LEFT JOIN (
        SELECT device_id, count(*) f_count, sum(download_bytes) f_down,
               sum(upload_bytes) f_up, sum(packets) f_pkts
        FROM flows GROUP BY device_id
    ) f ON f.device_id = d.device_id
    LEFT JOIN (
        SELECT device_id, sum(download_bytes) s_down, sum(upload_bytes) s_up
        FROM traffic_samples GROUP BY device_id
    ) t ON t.device_id = d.device_id
    ORDER BY d.device_id
    """
)
rows = cur.fetchall()
print("device_id | dev_up | dev_down | dev_pkts | flows | fl_down | fl_up | fl_pkts | sam_down | sam_up")
for r in rows:
    print(" | ".join(str(x) for x in r))

cur.close()
conn.close()