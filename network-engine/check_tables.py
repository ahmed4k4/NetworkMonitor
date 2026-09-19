import psycopg
conn = psycopg.connect('postgresql://postgres:12345678@localhost:5432/network_control')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
for row in cur.fetchall():
    print(row[0])
conn.close()