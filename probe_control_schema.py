from database.connection import get_connection, return_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        for table in ["network_rules", "speed_limits", "data_limits", "firewall_rules", "devices"]:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
                """,
                (table,),
            )
            print(f"=== {table} ===")
            for row in cur.fetchall():
                print(f"  {row[0]:24} {row[1]:20} null={row[2]:3} default={row[3]}")
            print()
finally:
    return_connection(conn)