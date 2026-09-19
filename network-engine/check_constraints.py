from database.connection import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'flows'::regclass")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()