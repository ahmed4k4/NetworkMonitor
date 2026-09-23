import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1) Grep engine.py + flow/ + analytics/attribution.py for flows INSERT and device_id sourcing
here = os.path.dirname(os.path.abspath(__file__))
for rel in ["engine.py", "flow", "analytics/attribution.py", "database/repository.py", "models"]:
    p = os.path.join(here, rel)
    if os.path.isfile(p):
        src = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"(?P<line>.*(INSERT INTO flows|save_flow|device_id\s*=|_attribute_and_save_flow).*)", src):
            ln = m.group("line").strip()
            if ln:
                print(f"{rel}: {ln[:160]}")
    elif os.path.isdir(p):
        for root, _, files in os.walk(p):
            for f in files:
                if f.endswith(".py"):
                    fp = os.path.join(root, f)
                    src = open(fp, encoding="utf-8", errors="replace").read()
                    for m in re.finditer(r"(?P<line>.*(INSERT INTO flows|save_flow|device_id\s*=|_attribute_and_save_flow).*)", src):
                        ln = m.group("line").strip()
                        if ln:
                            print(f"{os.path.relpath(fp, here)}: {ln[:160]}")

# 2) Live DB evidence: flows NULL device_id, recent samples, device rows
try:
    from database.connection import get_connection, return_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM flows WHERE device_id IS NULL")
    print("FLOWS NULL device_id count:", cur.fetchone()[0])
    cur.execute("""SELECT device_id, count(*) FROM flows WHERE device_id IS NULL
                   GROUP BY device_id ORDER BY count(*) DESC LIMIT 5""")
    print("NULL groups:", cur.fetchall())
    cur.execute("SELECT count(*) FROM traffic_samples")
    print("traffic_samples rows:", cur.fetchone()[0])
    cur.execute("SELECT count(*) FROM devices")
    print("devices rows:", cur.fetchone()[0])
    return_connection(conn)
except Exception as e:
    print("DB probe error:", e)
