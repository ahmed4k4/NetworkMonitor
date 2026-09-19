from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='devices' ORDER BY ordinal_position")
print("devices cols:", [r[0] for r in cur.fetchall()])
for t in ["traffic_samples", "usage_daily", "device_app_usage", "device_domain_usage", "device_category_usage", "device_protocol_usage", "device_activity_timeline", "device_peaks", "flows"]:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (t,))
    print(t, "cols:", [r[0] for r in cur.fetchall()])
return_connection(c)