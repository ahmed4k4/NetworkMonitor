import io, sys, psycopg
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
from config import database_config

c = psycopg.connect(host=database_config.host, port=database_config.port,
                    dbname=database_config.database, user=database_config.user,
                    password=database_config.password, autocommit=True)
cur = c.cursor()

# (table, timestamp_column, device column) for dev_002 freshness check
checks = [
    ("device_app_usage", "hour_start"),
    ("device_domain_usage", "hour_start"),
    ("device_category_usage", "hour_start"),
    ("device_protocol_usage", "hour_start"),
    ("device_activity_timeline", "hour_start"),
    ("sni_observations", "observed_at"),
    ("device_peaks", "peak_at"),
]
for t, col in checks:
    cur.execute(f"SELECT MAX({col}), MIN({col}), COUNT(*) FROM {t} WHERE device_id='dev_002'")
    row = cur.fetchone()
    print(f"{t}: max={row[0]} min={row[1]} count={row[2]}")

# Now(): what NOW() is relative
cur.execute("SELECT NOW()")
print("NOW() =", cur.fetchone()[0])
c.close()