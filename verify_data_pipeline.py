import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "network-engine"))
from database.connection import get_pool

pool = get_pool()
with pool.connection() as c:
    # Show real columns for the tables we inspect
    for t in ("traffic_samples", "connections", "dns_queries"):
        rows = c.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
            (t,),
        ).fetchall()
        print(f"{t} columns: {[r[0] for r in rows]}")

    r = c.execute(
        "SELECT count(*), coalesce(max(last_seen), NULL) "
        "FROM flows WHERE state='ACTIVE'"
    ).fetchone()
    print(f"flows ACTIVE count={r[0]} max_last_seen={r[1]}")

    r = c.execute("SELECT count(*), coalesce(max(last_seen), NULL) FROM flows").fetchone()
    print(f"flows TOTAL count={r[0]} max_last_seen={r[1]}")

    r = c.execute("SELECT count(*) FROM traffic_samples").fetchone()
    print(f"traffic_samples count={r[0]}")

    r = c.execute("SELECT count(*) FROM connections").fetchone()
    print(f"connections count={r[0]}")

    r = c.execute(
        "SELECT count(*), count(*) FILTER (WHERE vendor IS NOT NULL AND vendor != '') FROM devices"
    ).fetchone()
    print(f"devices total={r[0]} with_vendor={r[1]}")

    r = c.execute("SELECT count(*) FROM dns_queries").fetchone()
    print(f"dns_queries count={r[0]}")

    for t in ("device_app_usage", "device_category_usage", "device_protocol_usage", "device_domain_usage"):
        r = c.execute(f"SELECT count(*) FROM {t}").fetchone()
        print(f"{t} rows={r[0]}")

    for t in ("device_peaks", "device_activity_timeline"):
        r = c.execute(f"SELECT count(*) FROM {t}").fetchone()
        print(f"{t} rows={r[0]}")

    r = c.execute(
        "SELECT count(*) FROM flows WHERE packets < 0 OR bytes < 0 OR upload_bytes < 0 OR download_bytes < 0"
    ).fetchone()
    print(f"flows with negative counters (should be 0) = {r[0]}")