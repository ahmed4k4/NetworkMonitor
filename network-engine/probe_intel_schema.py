from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()
for t in ["device_app_usage", "device_domain_usage", "device_category_usage",
          "device_protocol_usage", "sni_observations", "device_peaks",
          "device_activity_timeline", "devices", "traffic_samples", "dns_queries"]:
    cur.execute("""
        SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)
    """, (t,))
    exists = cur.fetchone()[0]
    if not exists:
        print(t, "MISSING")
        continue
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name=%s ORDER BY ordinal_position
    """, (t,))
    cols = [r[0] for r in cur.fetchall()]
    print(t, "=>", cols)
return_connection(c)