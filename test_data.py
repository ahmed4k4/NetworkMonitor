import psycopg

conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')
with conn.cursor() as cur:
    # Check devices
    cur.execute('SELECT device_id, mac_address, ip_address, total_upload, total_download FROM devices;')
    devices = cur.fetchall()
    print('Devices:')
    for d in devices:
        print(f'  {d}')
    
    # Check usage_daily
    cur.execute('SELECT device_id, day_start, download_bytes, upload_bytes FROM usage_daily ORDER BY day_start DESC LIMIT 10;')
    usage = cur.fetchall()
    print('\nUsage Daily (recent):')
    for u in usage:
        print(f'  {u}')
    
    # Check usage_hourly
    cur.execute('SELECT device_id, hour_start, download_bytes, upload_bytes FROM usage_hourly ORDER BY hour_start DESC LIMIT 10;')
    usage_h = cur.fetchall()
    print('\nUsage Hourly (recent):')
    for u in usage_h:
        print(f'  {u}')
    
    # Check usage_monthly
    cur.execute('SELECT device_id, month_start, download_bytes, upload_bytes FROM usage_monthly ORDER BY month_start DESC LIMIT 10;')
    usage_m = cur.fetchall()
    print('\nUsage Monthly (recent):')
    for u in usage_m:
        print(f'  {u}')
    
    # Check for timezone in traffic_samples
    cur.execute('SELECT device_id, sampled_at, download_bytes, upload_bytes FROM traffic_samples ORDER BY sampled_at DESC LIMIT 5;')
    samples = cur.fetchall()
    print('\nTraffic Samples (recent):')
    for s in samples:
        print(f'  {s}')
    
    # Check CURRENT_DATE vs actual date
    cur.execute("SELECT NOW(), CURRENT_DATE, date_trunc('day', NOW())::date;")
    print('\nDate check:', cur.fetchone())

conn.close()