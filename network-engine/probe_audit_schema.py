from database.connection import get_connection, return_connection

c = get_connection()
try:
    with c.cursor() as cur:
        cur.execute(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_name IN ('flows','connections') ORDER BY table_name, ordinal_position"
        )
        cur_table = None
        for table, col, dtype in cur.fetchall():
            if table != cur_table:
                print(f"\n[{table}]")
                cur_table = table
            print(f"  {col:<22} {dtype}")
finally:
    return_connection(c)
print("\nDONE")