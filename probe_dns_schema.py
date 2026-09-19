import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import psycopg

c = psycopg.connect("host=127.0.0.1 port=5432 dbname=network_control user=postgres password=12345678")
cur = c.cursor()

for t in ["dns_queries", "device_domain_usage", "device_app_usage", "sni_observations", "flows"]:
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position",
        (t,),
    )
    print("=== %s ===" % t)
    for r in cur.fetchall():
        print("  ", r[0], r[1])

cur.execute("SELECT * FROM dns_queries ORDER BY queried_at DESC LIMIT 5")
print("\n=== dns_queries sample ===")
for r in cur.fetchall():
    print("  ", r)

cur.execute("SELECT * FROM device_domain_usage ORDER BY hour_start DESC LIMIT 5")
print("\n=== device_domain_usage sample ===")
for r in cur.fetchall():
    print("  ", r)

cur.execute("SELECT * FROM device_app_usage ORDER BY hour_start DESC LIMIT 5")
print("\n=== device_app_usage sample ===")
for r in cur.fetchall():
    print("  ", r)

c.close()