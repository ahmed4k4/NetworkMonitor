import io, sys, psycopg
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
from config import database_config

c = psycopg.connect(host=database_config.host, port=database_config.port,
                    dbname=database_config.database, user=database_config.user,
                    password=database_config.password, autocommit=True)
cur = c.cursor()

for t in ["traffic_samples", "sni_observations"]:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (t,))
    print(f"\n{t}:")
    for r in cur.fetchall():
        print(f"  {r[0]:25s} {r[1]}")

c.close()