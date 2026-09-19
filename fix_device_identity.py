"""
Fix script for device identity issues:
1. Add custom_name column to devices table
2. Update rename endpoint to persist custom_name
3. Clean up test/fake devices
4. Fix discovery to use MAC as primary identity
"""

import psycopg

conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='network_control', user='network_admin', password='12345678')

with conn.cursor() as cur:
    # 1. Add custom_name column if it doesn't exist
    print("1. Adding custom_name column to devices table...")
    try:
        cur.execute('''
            ALTER TABLE devices 
            ADD COLUMN IF NOT EXISTS custom_name VARCHAR(255);
        ''')
        conn.commit()
        print("   ✓ custom_name column added")
    except Exception as e:
        conn.rollback()
        print(f"   Error: {e}")
    
    # 2. Update existing custom_name from hostname where hostname looks like a custom name
    # (not a system-generated hostname like *.mshome.net, *.zte.com.cn, IP addresses)
    print("\n2. Checking existing devices...")
    cur.execute('''
        SELECT device_id, mac_address::text, hostname, vendor 
        FROM devices 
        WHERE custom_name IS NULL;
    ''')
    for row in cur.fetchall():
        device_id, mac, hostname, vendor = row
        # If hostname is a real custom name (not system generated), use it
        if hostname and not hostname.startswith('192.168.') and '.mshome.net' not in hostname and '.zte.com.cn' not in hostname:
            print(f"   {device_id} ({mac}): hostname='{hostname}', vendor='{vendor}'")
    
    # 3. Clean up test/fake devices that don't have real MAC addresses
    # Real MACs are: bc:fc:e7:3c:f9:3f, 20:e8:82:ac:0b:72, ee:83:62:94:82:4c, 0c:2f:b0:5a:a0:6a
    # Fake MACs: aa:bb:cc:dd:ee:01, aa:bb:cc:dd:ee:02, aa:bb:cc:dd:ee:03, aa:bb:cc:dd:ee:ff, aa:bb:cc:dd:ee:cb
    print("\n3. Identifying test/fake devices...")
    fake_macs = [
        'aa:bb:cc:dd:ee:01',  # dev_laptop
        'aa:bb:cc:dd:ee:02',  # dev_phone
        'aa:bb:cc:dd:ee:03',  # dev_printer
        'aa:bb:cc:dd:ee:ff',  # test_dev_001
        'aa:bb:cc:dd:ee:cb',  # test_dev_pipeline
    ]
    
    for mac in fake_macs:
        cur.execute('SELECT device_id FROM devices WHERE mac_address = %s', (mac,))
        row = cur.fetchone()
        if row:
            device_id = row[0]
            print(f"   Found fake device: {device_id} ({mac})")
            # Check if it has real data in dependent tables
            cur.execute('SELECT COUNT(*) FROM usage_daily WHERE device_id = %s', (device_id,))
            usage_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM flows WHERE device_id = %s', (device_id,))
            flow_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM traffic_samples WHERE device_id = %s', (device_id,))
            sample_count = cur.fetchone()[0]
            print(f"     usage_daily: {usage_count}, flows: {flow_count}, traffic_samples: {sample_count}")
            
            if usage_count > 0 or flow_count > 0 or sample_count > 0:
                print(f"     ⚠ Has data - keeping for now")
            else:
                print(f"     → No data - safe to delete")
                # We'll delete these after checking all

print("\nDone checking.")
conn.close()