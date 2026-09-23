import io, sys, psycopg, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
from config import database_config

c = psycopg.connect(host=database_config.host, port=database_config.port,
                    dbname=database_config.database, user=database_config.user,
                    password=database_config.password, autocommit=True)
cur = c.cursor()

def timestamp_col(table):
    cur.execute("SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (table,))
    cols = [r[0] for r in cur.fetchall()]
    # pick a timestamp-ish column
    for preferred in ["observed_at", "start_time", "timestamp", "first_seen", "created_at", "hour_start", "sampled_at", "queried_at"]:
        if preferred in cols:
            return preferred, cols
    return None, cols

for table in ["flows", "dns_queries", "traffic_samples"]:
    tcol, cols = timestamp_col(table)
    print("====", table, "cols=", cols, "timecol=", tcol)
    if tcol:
        try:
            cur.execute(f"SELECT device_id, MAX({tcol}), COUNT(*) FROM {table} GROUP BY device_id ORDER BY device_id")
            for r in cur.fetchall():
                print("   ", r[0], "max=", r[1], "count=", r[2])
        except Exception as e:
            print("   ERR", e)

c.close()

out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"], capture_output=True, text=True).stdout
print("PYTHON PROCESSES:\n", out[:2000])