import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from database.connection import get_connection, return_connection

def q(sql, params=None):
    c = get_connection()
    try:
        with c.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        return_connection(c)

print("=== BEFORE sweep: stale ACTIVE flows/connections (>300s) ===")
print("stale flows      :", q("SELECT COUNT(*) FROM flows WHERE state='ACTIVE' AND last_seen < NOW() - INTERVAL '300 seconds'"))
print("stale conns      :", q("SELECT COUNT(*) FROM connections WHERE state='ACTIVE' AND last_seen < NOW() - INTERVAL '300 seconds'"))
print("total ACTIVE flows:", q("SELECT COUNT(*) FROM flows WHERE state='ACTIVE'"))
print("total ACTIVE conns:", q("SELECT COUNT(*) FROM connections WHERE state='ACTIVE'"))

print("\n=== Calling get_active_flows() / get_active_connections() (sweeps stale) ===")
from database.repository import FlowRepository, ConnectionRepository
fr = FlowRepository()
cr = ConnectionRepository()
flows = fr.get_active_flows()
conns = cr.get_active_connections()
print("get_active_flows() returned", len(flows), "flows")
print("get_active_connections() returned", len(conns), "conns")

print("\n=== AFTER sweep ===")
print("total ACTIVE flows (now):", q("SELECT COUNT(*) FROM flows WHERE state='ACTIVE'"))
print("total ACTIVE conns (now):", q("SELECT COUNT(*) FROM connections WHERE state='ACTIVE'"))
print("\nDONE")