import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()
cur.execute("""
    SELECT tc.table_name, tc.constraint_type, kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_col
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    LEFT JOIN information_schema.constraint_column_usage ccu
      ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
    WHERE tc.table_schema = 'public'
    ORDER BY tc.table_name, tc.constraint_type, kcu.column_name
""")
for table, ctype, col, ref_table, ref_col in cur.fetchall():
    print(f"{table} | {ctype} | {col} | -> {ref_table}.{ref_col}")
return_connection(c)