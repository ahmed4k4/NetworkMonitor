import sys, io, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import psycopg
from config import database_config as dc

TARGET = "192.168.137.2"  # dev_002

def db():
    c = psycopg.connect(host=dc.host, port=dc.port, dbname=dc.database, user=dc.user, password=dc.password)
    return c

print("=== Starting sustained ping flood to dev_002 (%s) ===" % TARGET)
p = subprocess.Popen(["ping", "-t", "-n", "200", "-w", "10", TARGET],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    # Wait for traffic to accumulate
    time.sleep(20)

    c = db(); cur = c.cursor()

    print("\n=== dev_002 device row (during flood) ===")
    cur.execute("""
        SELECT device_id, state, last_seen, total_upload, total_download, total_packets, ip_address, mac_address
        FROM devices WHERE device_id='dev_002'
    """)
    print("  ", cur.fetchone())
    c.commit()

    print("\n=== dev_002 LIVE flows (this per-second snapshot) ===")
    cur.execute("""
        SELECT device_id, download_bytes, upload_bytes, packets, state, direction,
               source_ip, destination_ip, protocol, last_seen
        FROM flows
        WHERE device_id='dev_002' AND last_seen >= now() - interval '30 seconds'
        ORDER BY last_seen DESC LIMIT 20
    """)
    rows = cur.fetchall()
    print("  count:", len(rows))
    for r in rows:
        print("  ", r)
    c.commit()

    print("\n=== dev_002 device_peaks (live, last hour) ===")
    cur.execute("""
        SELECT device_id, peak_type, peak_value, peak_at, day, hour
        FROM device_peaks WHERE device_id='dev_002'
        ORDER BY peak_at DESC LIMIT 12
    """)
    for r in cur.fetchall():
        print("  ", r)
    c.commit()

    print("\n=== dev_002 current traffic (speed) sample ===")
    cur.execute("""
        SELECT device_id, sampled_at, download_bytes, upload_bytes, packets,
               download_speed_bps, upload_speed_bps, connections
        FROM traffic_samples
        WHERE device_id='dev_002'
        ORDER BY sampled_at DESC LIMIT 4
    """)
    for r in cur.fetchall():
        print("  ", r)
    c.commit()

    print("\n=== dev_002 activity (from analytics tables) ===")
    for tbl in ["activity", "device_activity", "network_activity"]:
        try:
            cur.execute("""
                SELECT column_name FROM information_schema.columns WHERE table_name=%s
            """, (tbl,))
            cols = [r[0] for r in cur.fetchall()]
            if cols:
                print("  table %s cols: %s" % (tbl, cols))
                cur.execute("SELECT * FROM %s WHERE device_id='dev_002' ORDER BY 1 DESC LIMIT 5" % tbl)
                for r in cur.fetchall():
                    print("     ", r)
                c.commit()
        except Exception as e:
            print("  %s err: %s" % (tbl, e))
            c.rollback()

    c.close()
finally:
    p.terminate()
    p.wait()
    print("\n(flood stopped)")
    print("\nDONE")
