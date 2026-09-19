"""Empirical live audit: compare API-returned displayed values against raw PostgreSQL records."""
import json, sys, time
import urllib.request

API = "http://127.0.0.1:8000"

def db(query, params=None):
    import psycopg2
    conn = psycopg2.connect(host="127.0.0.1", dbname="network_monitor", user="postgres", password="postgres")
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
            return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()

def api_get(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=10) as resp:
        return json.loads(resp.read().decode())

print("=" * 80)
print("AUDIT: DEVICES table vs /api/devices/ response")
print("=" * 80)
devices_db = db("""
    SELECT device_id, total_download, total_upload, total_packets,
           state, last_seen
    FROM devices ORDER BY device_id LIMIT 5
""")
for d in devices_db:
    print(f"  DB  {d['device_id']}: dl={d['total_download']} up={d['total_upload']} pkts={d['total_packets']} state={d['state']} last={d['last_seen']}")
print()
try:
    devs_api = api_get("/api/devices/")
    print(f"  API returned {len(devs_api)} devices. Fields per device:")
    if devs_api:
        sample = devs_api[0]
        print(f"  KEYS: {sorted(sample.keys())}")
        for k, v in sample.items():
            print(f"    {k} = {v!r}")
except Exception as e:
    print(f"  API error: {e}")
print()

print("=" * 80)
print("AUDIT: usage_daily vs device 'today' fields")
print("=" * 80)
today = db("""
    SELECT device_id, download_bytes, upload_bytes, packets
    FROM usage_daily
    WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date
    ORDER BY download_bytes DESC LIMIT 5
""")
for r in today:
    print(f"  DB usage_daily {r['device_id']}: dl={r['download_bytes']} up={r['upload_bytes']} pkts={r['packets']}")
print()

print("=" * 80)
print("AUDIT: applications analytics (device_app_usage) - does engine populate it?")
print("=" * 80)
app_rows = db("""
    SELECT COUNT(*) as cnt, COALESCE(SUM(total_bytes),0) as bytes, device_id
    FROM device_app_usage
    GROUP BY device_id
    ORDER BY bytes DESC LIMIT 5
""")
for r in app_rows:
    print(f"  device_app_usage {r['device_id']}: rows={r['cnt']} total_bytes={r['bytes']}")
print()

print("=" * 80)
print("AUDIT: domain analytics (device_domain_usage)")
print("=" * 80)
dom_rows = db("""
    SELECT COUNT(*) as cnt, COALESCE(SUM(total_bytes),0) as bytes, COALESCE(SUM(queries),0) as q
    FROM device_domain_usage
    WHERE hour_start > NOW() - INTERVAL '24 hours'
""")
for r in dom_rows:
    print(f"  device_domain_usage last 24h: rows={r['cnt']} total_bytes={r['bytes']} queries={r['q']}")
print()

print("=" * 80)
print("AUDIT: traffic_samples (drives chart & speeds)")
print("=" * 80)
ts = db("""
    SELECT COUNT(*) cnt,
           COALESCE(AVG(download_speed_bps),0) avg_dl_bps,
           COALESCE(AVG(upload_speed_bps),0) avg_up_bps,
           COALESCE(SUM(download_bytes),0) sum_dl,
           COALESCE(SUM(upload_bytes),0) sum_up
    FROM traffic_samples
    WHERE sampled_at > NOW() - INTERVAL '2 minutes'
""")
if ts:
    for r in ts:
        print(f"  traffic_samples (2min): rows={r['cnt']} avg_dl={r['avg_dl_bps']} avg_up={r['avg_up_bps']} sum_dl={r['sum_dl']} sum_up={r['sum_up']}")
else:
    print("  NO ROWS returned")

print()
print("=" * 80)
print("AUDIT: /api/system/status live")
print("=" * 80)
try:
    st = api_get("/api/system/status")
    for k in ["total_devices","online_devices","active_connections","active_flows",
              "total_download","total_upload","today_download","today_upload",
              "current_download_speed_bps","current_upload_speed_bps","peak_bandwidth_bps"]:
        print(f"  {k} = {st.get(k)}")
except Exception as e:
    print(f"  API error: {e}")