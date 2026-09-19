import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT device_id, application, category, confidence, hour_start, total_bytes, download_bytes, upload_bytes, connections FROM device_app_usage ORDER BY hour_start DESC LIMIT 20")
        print("=== device_app_usage (latest 20) ===")
        for r in cur.fetchall():
            print("  ", r)

        cur.execute("SELECT device_id, COUNT(*) FROM device_app_usage GROUP BY device_id")
        print("\napp usage by device:", cur.fetchall())

        cur.execute("SELECT device_id, application, category, confidence, hour_start, total_bytes FROM device_app_usage WHERE hour_start > NOW() - INTERVAL '24 hours' ORDER BY hour_start DESC")
        rows = cur.fetchall()
        print(f"\napp usage last 24h: {len(rows)} rows")
        for r in rows[:20]:
            print("  ", r)

        cur.execute("SELECT MIN(hour_start), MAX(hour_start) FROM device_app_usage")
        print("\napp usage time range:", cur.fetchone())

        cur.execute("SELECT device_id, COUNT(*) FROM device_domain_usage GROUP BY device_id")
        print("\ndomain usage by device:", cur.fetchall())

        cur.execute("SELECT MIN(hour_start), MAX(hour_start) FROM device_domain_usage")
        print("domain usage time range:", cur.fetchone())

        cur.execute("SELECT id, device_id, name, category, confidence FROM applications ORDER BY id LIMIT 20")
        print("\n=== applications table ===")
        print(cur.fetchall())

        cur.execute("SELECT id, name, category FROM domains ORDER BY id LIMIT 20")
        print("\n=== domains table (count+sample) ===")
        rows = cur.fetchall()
        print("count shown:", len(rows))
        for r in rows:
            print("  ", r)
except Exception as e:
    import traceback; traceback.print_exc()
    conn.rollback()
finally:
    from database.connection import close_pool
    close_pool()