"""Temporary audit helper. Check DB connectivity, schema, users, and counts."""
import sys
sys.path.insert(0, "e:/NetworkMonitor/network-engine")
import psycopg
from config import database_config

print("DB config:", database_config.host, database_config.port,
      database_config.database, database_config.user, "pass=***")
try:
    c = psycopg.connect(
        host=database_config.host, port=database_config.port,
        dbname=database_config.database, user=database_config.user,
        password=database_config.password)
    cur = c.cursor()
    cur.execute("select version()")
    print("connected:", cur.fetchone()[0][:50])
    # list tables
    cur.execute("""
        select table_name from information_schema.tables
        where table_schema='public' order by table_name
    """)
    print("TABLES:", [t[0] for t in cur.fetchall()])
    cur.execute("select count(*) from devices")
    print("devices:", cur.fetchone()[0])
    cur.execute("select username, role from users order by username")
    print("users:", cur.fetchall())
    c.close()
except Exception as e:
    print("DB ERROR:", repr(e))