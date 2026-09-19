"""Comprehensive backend verification: imports, pool, migrations, repositories, API routes."""
import sys, os, importlib, traceback

# Add network-engine directory to path
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "network-engine"))

results = []

def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))
        traceback.print_exc()

def test_imports():
    mods = [
        "engine", "main", "config", "logger",
        "api.app", "api.auth", "api.security", "api.schemas", "api.websocket",
        "api.routes.devices", "api.routes.traffic", "api.routes.flows",
        "api.routes.dns", "api.routes.applications", "api.routes.control",
        "api.routes.alerts", "api.routes.analytics", "api.routes.reports",
        "api.routes.system", "api.routes.data_management", "api.routes.auth",
        "database.connection", "database.migrations", "database.repository",
        "database.retention", "database.aggregation", "database.audit",
        "discovery.scanner", "discovery.oui",
        "capture.parser", "capture.sniffer",
        "control.engine", "control.firewall", "control.priority",
        "control.profiles", "control.qos", "control.quotas",
        "control.rules", "control.scheduler", "control.state", "control.windows",
        "flow.bandwidth", "flow.connections", "flow.device_stats", "flow.manager",
        "analytics.applications", "analytics.attribution", "analytics.categories",
        "analytics.distribution", "analytics.dns", "analytics.domains",
        "analytics.engine", "analytics.geo", "analytics.protocols", "analytics.top_talkers",
        "models", "events", "alerts",
    ]
    for m in mods:
        importlib.import_module(m)
    print("   Imported", len(mods), "modules OK")

def test_pool():
    from database.connection import get_pool
    pool = get_pool()
    assert pool is not None, "pool is None"
    with pool.connection() as conn:
        cur = conn.execute("SELECT 1")
        assert cur.fetchone()[0] == 1, "SELECT 1 failed"
    print("   Pool created and SELECT 1 works")

def test_migrations():
    from database.migrations import initialize_database
    initialize_database()
    print("   Migrations (initialize_database) ran")

def test_repositories():
    from database.repository import (
        DeviceRepository, TrafficRepository, FlowRepository,
        ConnectionRepository, DeviceIntelligenceRepository,
        get_connection, return_connection,
    )
    for cls in (DeviceRepository, TrafficRepository, FlowRepository,
                ConnectionRepository, DeviceIntelligenceRepository):
        assert cls is not None
    assert callable(get_connection) and callable(return_connection)
    print("   Repository classes and connection funcs available")

def test_app_routes():
    from api.app import app
    # FastAPI 0.141+ uses lazy _IncludedRouter proxies; count effective routes
    try:
        eff = list(app.router.effective_route_contexts())
        count = len(eff)
    except Exception:
        # fallback: count route list including nested
        count = 0
        def walk(routes):
            n = 0
            for r in routes:
                if hasattr(r, "effective_route_contexts"):
                    n += sum(1 for _ in r.effective_route_contexts())
                else:
                    n += 1
            return n
        count = walk(app.router.routes)
    assert count >= 60, f"Only {count} effective routes registered"
    print(f"   FastAPI app has {count} effective routes")

check("Imports", test_imports)
check("ConnectionPool", test_pool)
check("Migrations", test_migrations)
check("Repositories", test_repositories)
check("AppRoutes", test_app_routes)

print("\n=== RESULTS ===")
fails = 0
for name, status, detail in results:
    print(f"{status:5s} {name} {detail}")
    if status == "FAIL":
        fails += 1
print(f"\nTOTAL: {len(results)} checks, {fails} failures")
sys.exit(1 if fails else 0)