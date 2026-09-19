import psycopg
conn = psycopg.connect('postgresql://postgres:12345678@localhost:5432/network_control')
cur = conn.cursor()

# Check config/settings
cur.execute("SELECT * FROM settings")
rows = cur.fetchall()
col_names = [desc[0] for desc in cur.description]
print("settings columns:", col_names)
for row in rows:
    print(row)

print("\n---")

# Check interfaces
cur.execute("SELECT * FROM interfaces")
rows = cur.fetchall()
col_names = [desc[0] for desc in cur.description]
print("interfaces columns:", col_names)
for row in rows:
    print(row)

conn.close()