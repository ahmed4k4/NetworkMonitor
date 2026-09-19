import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()

print("=== devices columns (NOT NULL) ===")
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'devices'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20} {row[1]:15} nullable={row[2]:5} default={row[3]}")

print("\n=== device_peaks columns (NOT NULL) ===")
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'device_peaks'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20} {row[1]:15} nullable={row[2]:5} default={row[3]}")

print("\n=== current devices rows ===")
cur.execute("SELECT device_id, mac_address, ip_address, state, first_seen, last_seen FROM devices ORDER BY device_id")
for row in cur.fetchall():
    print(f"  {row}")

print("\n=== current device_peaks rows ===")
cur.execute("SELECT * FROM device_peaks ORDER BY id DESC LIMIT 5")
cols = [d[0] for d in cur.description]
print(f"  cols: {cols}")
for row in cur.fetchall():
    print(f"  {row}")

return_connection(c)