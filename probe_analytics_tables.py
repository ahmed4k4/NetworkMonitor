import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
from database.connection import get_connection

c = get_connection()
rows = c.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='public' "
    "AND (table_name LIKE '%app%' OR table_name LIKE '%domain%' "
    "OR table_name LIKE '%protocol%' OR table_name LIKE '%categor%' "
    "OR table_name LIKE '%activ%' OR table_name LIKE '%peak%') "
    "ORDER BY table_name"
).fetchall()
print("tables:", [r[0] for r in rows])
c.close()