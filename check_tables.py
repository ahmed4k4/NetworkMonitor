import sys
sys.path.insert(0, 'E:/NetworkMonitor/network-engine')
import psycopg
from config import database_config

conn = psycopg.connect(
    host=database_config.host,
    port=database_config.port,
    dbname=database_config.database,
    user=database_config.user,
    password=database_config.password,
)

with conn.cursor() as cur:
    # Check tables
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name""")
    tables = cur.fetchall()
    print('Tables:', [t[0] for t in tables])
    
    # Check usage_daily table structure
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'usage_daily' ORDER BY ordinal_position""")
    print('\nusage_daily columns:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')
    
    # Check traffic_samples table structure
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'traffic_samples' ORDER BY ordinal_position""")
    print('\ntraffic_samples columns:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')
    
    # Check data_limits table structure
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'data_limits' ORDER BY ordinal_position""")
    print('\ndata_limits columns:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')
    
    # Check speed_limits table structure
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'speed_limits' ORDER BY ordinal_position""")
    print('\nspeed_limits columns:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')
    
    # Check devices table structure
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'devices' ORDER BY ordinal_position""")
    print('\ndevices columns:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')

conn.close()