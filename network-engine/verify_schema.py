import sys
sys.path.insert(0, '.')
from database.connection import get_connection, return_connection
c = get_connection()
cur = c.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
return_connection(c)
for t in tables:
    print(t)