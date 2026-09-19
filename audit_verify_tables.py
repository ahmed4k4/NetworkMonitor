"""Confirm actual usage/analytics table names + repo write targets."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "network-engine"))
from database.connection import get_connection, return_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        # All tables in public schema
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE'
            ORDER BY table_name
        """)
        print("ALL TABLES:")
        for (t,) in cur.fetchall():
            print("  ", t)
finally:
    conn.rollback()
    return_connection(conn)

print("\n--- Repository INSERT targets (from source) ---")
import re
src = open(os.path.join(os.path.dirname(__file__), "network-engine", "database", "repository.py"), encoding="utf-8").read()
for m in re.finditer(r"INSERT INTO\s+([a-zA-Z_0-9]+)", src):
    print("  INSERT INTO", m.group(1))