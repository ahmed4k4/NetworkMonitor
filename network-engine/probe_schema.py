from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()
cur.execute("""
    SELECT table_name, column_name, data_type, is_generated, generation_expression
    FROM information_schema.columns
    WHERE table_name LIKE 'device%usage'
    ORDER BY table_name, ordinal_position
""")
for r in cur.fetchall():
    print(r)
return_connection(c)