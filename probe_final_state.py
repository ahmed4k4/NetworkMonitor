import io, sys, psycopg, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
from config import database_config

c = psycopg.connect(host=database_config.host, port=database_config.port,
                    dbname=database_config.database, user=database_config.user,
                    password=database_config.password, autocommit=True)
cur = c.cursor()

cur.execute("SELECT NOW()")
now = cur.fetchone()[0]
print("NOW() =", now)

checks = [
    ("traffic_samples", "sampled_at", None),
    ("flows", "last_seen", None),
    ("dns_queries", "queried_at", None),
    ("device_app_usage", "hour_start", None),
    ("device_domain_usage", "hour_start", None),
    ("device_category_usage", "hour_start", None),
    ("device_protocol_usage", "hour_start", None),
    ("device_activity_timeline", "hour_start", None),
    ("sni_observations", "observed_at", None),
    ("device_peaks", "peak_at", None),
    ("usage_daily", "day_start", None),
]
print("\nTABLE FRESHNESS (global max):")
for t, col, _ in checks:
    try:
        cur.execute(f"SELECT MAX({col}), COUNT(*) FROM {t}")
        r = cur.fetchone()
        print(f"  {t:28s} max={r[0]}  count={r[1]}")
    except Exception as e:
        print(f"  {t:28s} ERR {e}")

print("\nCURRENT DEVICE TOTALS:")
cur.execute("SELECT device_id, total_upload, total_download, total_packets, state, last_seen FROM devices ORDER BY device_id")
for r in cur.fetchall():
    print("  ", r)

c.close()

out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"], capture_output=True, text=True).stdout
print("\nPYTHON PROCESSES:\n", out[:1500])