import psycopg2

c = psycopg2.connect(host="127.0.0.1", port=5432, dbname="network_control", user="postgres", password="12345678")
cur = c.cursor()

print("=== network_rules ===")
cur.execute("SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='network_rules' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r)

print("=== devices ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='devices' ORDER BY ordinal_position")
print([r[0] for r in cur.fetchall()])

c.close()
