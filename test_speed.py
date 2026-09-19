from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM traffic_samples WHERE sampled_at > NOW() - INTERVAL \'2 minutes\'')
        print(f'Recent samples: {cur.fetchone()[0]}')
        cur.execute('SELECT device_id, download_speed_bps, upload_speed_bps, sampled_at FROM traffic_samples WHERE sampled_at > NOW() - INTERVAL \'2 minutes\' ORDER BY device_id, sampled_at DESC')
        for row in cur.fetchall():
            print(f'  {row}')
finally:
    conn.close()