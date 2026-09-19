import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "network-engine"))
from database.connection import get_pool

pool = get_pool()
with pool.connection() as conn:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' ORDER BY table_name"
    ).fetchall()
    names = [r[0] for r in rows]
    print("TABLES:", names)

    for t in (
        "devices",
        "flows",
        "traffic_samples",
        "applications",
        "domains",
        "dns_queries",
        "network_rules",
        "speed_limits",
        "data_limits",
        "firewall_rules",
        "alerts",
        "interfaces",
        "events",
        "device_activity_timeline",
        "device_peaks",
        "device_app_usage",
        "device_category_usage",
        "device_domain_usage",
        "device_protocol_usage",
        "usage_daily",
        "usage_hourly",
        "usage_monthly",
        "connections",
        "sni_observations",
        "settings",
        "users",
    ):
        c = conn.execute(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s",
            (t,),
        ).fetchone()[0]
        print(f"  {t}: {c} columns")