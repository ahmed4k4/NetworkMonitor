import io, sys, psycopg
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
from config import database_config

c = psycopg.connect(host=database_config.host, port=database_config.port,
                    dbname=database_config.database, user=database_config.user,
                    password=database_config.password, autocommit=True)
cur = c.cursor()

tables = ["device_app_usage", "device_domain_usage", "device_category_usage",
          "device_protocol_usage", "device_activity_timeline", "sni_observations",
          "device_peaks", "usage_daily", "traffic_samples", "flows", "dns_queries"]
for t in tables:
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename=%s", (t,))
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) FROM " + t)
        n = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM " + t + " WHERE device_id='dev_002'")
        d = cur.fetchone()[0]
        print(t, "total=", n, "dev002=", d)
    else:
        print(t, "TABLE DOES NOT EXIST")
c.close()