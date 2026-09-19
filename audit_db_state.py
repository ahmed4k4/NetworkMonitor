import sys, os

sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.connection import get_connection, return_connection

conn = get_connection()
with conn.cursor() as c:
    c.execute(
        "SELECT state, COUNT(*), MIN(last_seen)::text, MAX(last_seen)::text FROM flows GROUP BY state ORDER BY count DESC"
    )
    print("FLOW STATES:", c.fetchall())

    c.execute(
        "SELECT COUNT(*) FROM flows WHERE state='ACTIVE' AND last_seen < NOW() - INTERVAL '1 day'"
    )
    print("ACTIVE stale >1day:", c.fetchone()[0])

    c.execute(
        "SELECT to_char(day_start,'YYYY-MM-DD'), COUNT(*), SUM(download_bytes), SUM(upload_bytes) "
        "FROM usage_daily GROUP BY day_start ORDER BY day_start DESC LIMIT 5"
    )
    print("USAGE_DAILY:", c.fetchall())

    c.execute(
        "SELECT to_char(hour_start,'YYYY-MM-DD HH24'), COUNT(*), SUM(download_bytes) "
        "FROM usage_hourly GROUP BY hour_start ORDER BY hour_start DESC LIMIT 8"
    )
    print("USAGE_HOURLY:", c.fetchall())

    c.execute("SELECT COUNT(*), MAX(sampled_at)::text FROM traffic_samples")
    print("TRAFFIC_SAMPLES total/last:", c.fetchone())

    c.execute("SELECT COUNT(*) FROM dns_queries")
    print("DNS_QUERIES:", c.fetchone()[0])

    c.execute("SELECT COUNT(*) FROM device_domain_usage")
    print("DEVICE_DOMAIN_USAGE:", c.fetchone()[0])

    c.execute("SELECT COUNT(*) FROM device_app_usage")
    print("DEVICE_APP_USAGE:", c.fetchone()[0])

return_connection(conn)