import sys
sys.path.insert(0, r'E:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection

c = get_connection()
cur = c.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='traffic_samples' ORDER BY ordinal_position")
for name, dtype in cur.fetchall():
    print(name, dtype)
return_connection(c)