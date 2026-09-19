import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.connection import get_connection

c = get_connection()
rows = c.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='flows' ORDER BY ordinal_position"
).fetchall()
print("flows columns:", [r[0] for r in rows])
c.close()