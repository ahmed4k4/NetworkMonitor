import os
from database.connection import get_pool, return_connection, close_pool

conn = get_pool().getconn()
cur = conn.cursor()
cur.execute("SELECT username, role, is_active FROM users ORDER BY username")
rows = cur.fetchall()
for r in rows:
    print("USER:", r)
conn.rollback()
return_connection(conn)
close_pool()

print("ADMIN_PASSWORD env:", repr(os.getenv("ADMIN_PASSWORD")))
print("OPERATOR_PASSWORD env:", repr(os.getenv("OPERATOR_PASSWORD")))
print("VIEWER_PASSWORD env:", repr(os.getenv("VIEWER_PASSWORD")))