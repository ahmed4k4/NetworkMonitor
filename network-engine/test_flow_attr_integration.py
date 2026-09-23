import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from datetime import datetime, timezone
from models.flow import Flow
from database.repository import DeviceIntelligenceRepository
from database.connection import get_connection
from analytics.attribution import AttributionEngine

from database.connection import return_connection

# Pick a REAL registered device at runtime (dev_001 was a removed seed device).
conn_probe = get_connection()
try:
    with conn_probe.cursor() as cur:
        cur.execute("SELECT device_id FROM devices ORDER BY device_id LIMIT 1")
        _row = cur.fetchone()
finally:
    return_connection(conn_probe)
assert _row, "No devices table rows to test flow attribution against"
DEV = _row[0]

DOMAIN = "test-integration.example.com"
IP = "203.0.113.77"

repo = DeviceIntelligenceRepository()
attr = AttributionEngine()

# 1) Store a DNS response mapping for the device (as the engine now does)
repo.save_dns_query(DEV, DOMAIN, "1", response_ip=IP)

# 2) Simulate a closed flow toward that IP
flow = Flow(
    key="t1",
    source_ip="192.168.137.10",
    destination_ip=IP,
    source_port=55000,
    destination_port=443,
    protocol="TCP",
    interface="Ethernet",
    started_at=datetime.now(timezone.utc),
    last_seen=datetime.now(timezone.utc),
    packets=10,
    bytes=50000,
    upload_bytes=5000,
    download_bytes=45000,
    direction="DOWNLOAD",
    device_id=DEV,
    state="CLOSED",
)
flow.sni = None

# 3) Replicate the engine's correlation lookup
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT domain FROM dns_queries
            WHERE device_id = %s
              AND response_ip = %s
              AND queried_at >= %s - INTERVAL '60 minutes'
              AND queried_at <= %s + INTERVAL '5 minutes'
            ORDER BY queried_at DESC
            LIMIT 1
            """,
            (DEV, flow.destination_ip, flow.started_at, flow.started_at),
        )
        row = cur.fetchone()
        domain = row[0] if row else None
        print("Resolved flow domain:", domain)
        assert domain == DOMAIN
finally:
    from database.connection import return_connection
    return_connection(conn)

# 4) Run the attribution used by the engine
result = attr.analyze(
    device_id=DEV,
    destination_ip=flow.destination_ip,
    domain=domain,
    sni=flow.sni,
    protocol=flow.protocol,
    port=flow.destination_port,
    bytes_transferred=flow.bytes,
)
print("Attribution result:", result.application, result.category, result.confidence)
assert result.confidence in ("HIGH", "MEDIUM", "LOW")

hour_start = flow.started_at.replace(minute=0, second=0, microsecond=0)
evidence = [
    {"source": e.source, "value": e.value, "weight": e.weight,
     "confidence": e.confidence, "details": e.details}
    for e in result.evidence
]

repo.save_app_usage(DEV, result.application, result.category, result.confidence, hour_start, 45000, 5000, 1, evidence)
repo.save_domain_usage(DEV, domain, result.category, hour_start, 45000, 5000, 1, 1, result.confidence, evidence)

# 5) Verify persisted usage
with conn.cursor() as cur:
    cur.execute("SELECT application, category, confidence, total_bytes FROM device_app_usage WHERE device_id=%s AND application=%s ORDER BY hour_start DESC LIMIT 1", (DEV, result.application))
    print("app usage row:", cur.fetchone())

    cur.execute("SELECT domain, confidence, total_bytes, queries FROM device_domain_usage WHERE device_id=%s AND domain=%s ORDER BY hour_start DESC LIMIT 1", (DEV, domain))
    print("domain usage row:", cur.fetchone())

print("\nINTEGRATION PIPELINE TEST PASSED")