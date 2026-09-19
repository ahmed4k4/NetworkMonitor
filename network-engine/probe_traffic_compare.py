from database.connection import get_connection, return_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT d.device_id,
           d.total_upload, d.total_download, d.total_packets,
           COALESCE(ts.ul, 0) AS sum_upload,
           COALESCE(ts.dl, 0) AS sum_download,
           COALESCE(ts.pk, 0) AS sum_packets,
           ts.n AS sample_count
    FROM devices d
    LEFT JOIN (
        SELECT device_id,
               SUM(upload_bytes) AS ul,
               SUM(download_bytes) AS dl,
               SUM(packets) AS pk,
               COUNT(*) AS n
        FROM traffic_samples
        GROUP BY device_id
    ) ts ON ts.device_id = d.device_id
    ORDER BY (COALESCE(ts.dl,0) + COALESCE(ts.ul,0)) DESC
""")
rows = cur.fetchall()
print(f"{'device_id':15} {'total_ul':>12} {'sum_ul':>12} {'total_dl':>12} {'sum_dl':>12} {'total_pk':>10} {'sum_pk':>10} {'samples':>8}")
for r in rows:
    print(f"{str(r[0]):15} {str(r[1]):>12} {str(r[4]):>12} {str(r[2]):>12} {str(r[5]):>12} {str(r[3]):>10} {str(r[6]):>10} {str(r[7]):>8}")

return_connection(conn)