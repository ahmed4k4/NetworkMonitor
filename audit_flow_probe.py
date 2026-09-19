"""Comprehensive end-to-end data flow probe: compare API responses against PostgreSQL records."""

import sys, urllib.request, json, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "network-engine"))
from api.auth import create_access_token
from database.connection import get_connection, return_connection

TOKEN = create_access_token("admin", "ADMIN")
API = "http://127.0.0.1:8000"


def api_get(path):
    req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, "non-json"
    except Exception as ex:
        return -1, str(ex)


def db_q(sql, args=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            return cur.fetchall()
    finally:
        return_connection(conn)


print("=" * 70)
print("END-TO-END DATA FLOW AUDIT - VALUE PROBE (API vs Postgres)")
print("=" * 70)

# 1. devices table totals
print("\n--- 1. DEVICES: devices.total_* vs /api/devices upload/download ---")
try:
    rows = db_q("SELECT device_id, total_upload, total_download, state, last_seen::text FROM devices ORDER BY last_seen DESC LIMIT 5")
except Exception as e:
    print(f"DB error: {e}")
    rows = []

st, devices = api_get("/api/devices/")
for r in rows[:3]:
    if st == 200:
        match = [d for d in devices if d.get("device_id") == r[0]]
        if match:
            d = match[0]
            db_total = (r[1] or 0) + (r[2] or 0)
            api_total = (d.get("upload") or 0) + (d.get("download") or 0)
            matchflag = "OK" if abs(db_total - api_total) < 1 else "MISMATCH"
            print(f"  dev={r[0][:8]}: DB total_ul+dl={db_total}, API upload+download={api_total} [{matchflag}]")
        else:
            print(f"  dev={r[0][:8]}: in DB but NOT in /api/devices -> MISSING")

# 2. usage_daily vs /api/devices download_today/upload_today
print("\n--- 2. usage_daily (today) vs /api/devices download_today/upload_today ---")
try:
    today = db_q("SELECT device_id, download_bytes, upload_bytes FROM usage_daily WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date ORDER BY download_bytes DESC LIMIT 3")
except Exception as e:
    today = []

for t in today[:2]:
    m = [d for d in devices if d.get("device_id") == t[0]]
    if m:
        d = m[0]
        ok = (t[1] or 0) == (d.get("download_today") or 0) and (t[2] or 0) == (d.get("upload_today") or 0)
        print(f"  dev={t[0][:8]}: DB dl={t[1]},ul={t[2]} | API dl_today={d.get('download_today')},ul_today={d.get('upload_today')} [{'OK' if ok else 'MISMATCH'}]")
    else:
        print(f"  dev={t[0][:8]}: DB has row but not in /api/devices -> MISSING")

# 3. traffic_samples vs /api/traffic/recent
print("\n--- 3. traffic_samples latest vs /api/traffic/recent ---")
try:
    ts = db_q("SELECT device_id::text, download_bytes, upload_bytes, download_speed_bps, upload_speed_bps FROM traffic_samples ORDER BY sampled_at DESC LIMIT 3")
except Exception as e:
    ts = []

st, rec = api_get("/api/traffic/recent")
if st == 200 and ts and rec:
    a = rec[0]
    print(f"  API first sample: device={a.get('device_id')}, download={a.get('download')}, upload={a.get('upload')}, dl_speed={a.get('download_speed_bps')}, ul_speed={a.get('upload_speed_bps')}")
    t = ts[0]
    ok = (t[1] or 0) == (a.get("download") or 0)
    print(f"  DB first row: download={t[1]}, upload={t[2]}, dl_speed={t[3]}, ul_speed={t[4]} [{'OK' if ok else 'MISMATCH'}]")
else:
    print(f"  /api/traffic/recent -> status {st}")

# 4. flows vs /api/flows/active
print("\n--- 4. flows ACTIVE vs /api/flows/active ---")
try:
    fcnt = db_q("SELECT COUNT(*), COALESCE(SUM(bytes),0), COALESCE(SUM(upload_bytes),0), COALESCE(SUM(download_bytes),0) FROM flows WHERE state='ACTIVE'")[0]
except Exception as e:
    fcnt = (None, None, None, None)

st, flows = api_get("/api/flows/active")
if st == 200:
    api_bytes = sum((f.get("bytes") or 0) for f in flows)
    api_up = sum((f.get("upload") or 0) for f in flows)
    api_dl = sum((f.get("download") or 0) for f in flows)
    print(f"  DB: count={fcnt[0]}, bytes={fcnt[1]}, upload={fcnt[2]}, download={fcnt[3]}")
    print(f"  API: count={len(flows)}, bytes={api_bytes}, upload={api_up}, download={api_dl} (top 500)")
    if len(flows) >= 500:
        print("  NOTE: API caps at 500; DB count may exceed -> partial view")
else:
    print(f"  /api/flows/active -> status {st}")

# 5. domain analytics vs device_domain_usage
print("\n--- 5. device_domain_usage (24h) vs /api/analytics/domains ---")
try:
    dd = db_q("SELECT COUNT(*), COALESCE(SUM(total_bytes),0) FROM device_domain_usage WHERE hour_start > NOW() - INTERVAL '24 hours'")[0]
except Exception as e:
    dd = (None, None)

st, dom = api_get("/api/analytics/domains")
if st == 200:
    api_ct = len(dom)
    api_traffic = sum((x.get("traffic") or 0) for x in dom)
    print(f"  DB: rows={dd[0]}, traffic={dd[1]} | API: rows={api_ct}, traffic={api_traffic}")
    print(f"  Mismatch: rows={'OK' if (dd[0] or 0)==api_ct else 'MISMATCH'}, traffic={'OK' if (dd[1] or 0)==api_traffic else 'MISMATCH'}")
else:
    print(f"  /api/analytics/domains -> {st}")

# 6. app analytics vs device_app_usage
print("\n--- 6. device_app_usage (24h) vs /api/analytics/applications ---")
try:
    da = db_q("SELECT COUNT(*), COALESCE(SUM(total_bytes),0) FROM device_app_usage WHERE hour_start > NOW() - INTERVAL '24 hours'")[0]
except Exception as e:
    da = (None, None)

st, apps = api_get("/api/analytics/applications")
if st == 200:
    api_ct = len(apps)
    api_traffic = sum((x.get("traffic") or 0) for x in apps)
    print(f"  DB: rows={da[0]}, traffic={da[1]} | API: rows={api_ct}, traffic={api_traffic}")
    print(f"  Mismatch: rows={'OK' if (da[0] or 0)==api_ct else 'MISMATCH'}, traffic={'OK' if (da[1] or 0)==api_traffic else 'MISMATCH'}")
    if apps:
        print(f"  sample: {json.dumps(apps[0])[:200]}")
else:
    print(f"  /api/analytics/applications -> {st}")

# 7. usage_hourly vs /api/analytics/hourly
print("\n--- 7. usage_hourly (24h) vs /api/analytics/hourly ---")
try:
    uh = db_q("SELECT COUNT(*), COALESCE(SUM(download_bytes),0), COALESCE(SUM(upload_bytes),0) FROM usage_hourly WHERE hour_start > NOW() - INTERVAL '24 hours'")[0]
except Exception as e:
    uh = (None, None, None)

st, hr = api_get("/api/analytics/hourly")
if st == 200:
    print(f"  DB: rows={uh[0]}, dl={uh[1]}, ul={uh[2]} | API: rows={len(hr)}, dl={sum(x.get('download') or 0 for x in hr)}, ul={sum(x.get('upload') or 0 for x in hr)}")
else:
    print(f"  /api/analytics/hourly -> {st}")

# 8. usage_daily (30d) vs /api/analytics/daily
print("\n--- 8. usage_daily (30d) vs /api/analytics/daily ---")
try:
    ud = db_q("SELECT COUNT(*), COALESCE(SUM(download_bytes),0), COALESCE(SUM(upload_bytes),0) FROM usage_daily WHERE day_start > (NOW() AT TIME ZONE 'Africa/Cairo')::date - INTERVAL '30 days'")[0]
except Exception as e:
    ud = (None, None, None)

st, dl = api_get("/api/analytics/daily")
if st == 200:
    print(f"  DB: rows={ud[0]}, dl={ud[1]}, ul={ud[2]} | API: rows={len(dl)}, dl={sum(x.get('download') or 0 for x in dl)}, ul={sum(x.get('upload') or 0 for x in dl)}")
else:
    print(f"  /api/analytics/daily -> {st}")

# 9. device intelligence endpoints
print("\n--- 9. Device intelligence: /api/devices/{id}/intelligence ---")
if devices:
    did = devices[0]["device_id"]
    st, intel = api_get(f"/api/devices/{did}/intelligence?range=24h")
    if st == 200:
        print(f"  {did[:8]}: apps={len(intel.get('top_applications') or [])}, domains={len(intel.get('top_domains') or [])}, categories={len(intel.get('top_categories') or [])}, protocols={len(intel.get('top_protocols') or [])}, peaks={intel.get('peaks')}, total_dl={intel.get('total_download')}, total_ul={intel.get('total_upload')}")
    else:
        print(f"  /intelligence -> {st}")

# 10. devices page display fields
print("\n--- 10. Frontend-critical fields present in /api/devices ---")
if st == 200 and devices:
    d = devices[0]
    required = ["device_id","mac","ip","hostname","custom_name","vendor","interface","state","first_seen","last_seen","upload","download","download_today","upload_today","total_today","download_speed_bps","upload_speed_bps","current_speed_bps","usage_percentage","quota_bytes","quota_used_bytes","quota_remaining_bytes","quota_enabled","limit_id","download_limit_bps","upload_limit_bps","limit_enabled"]
    missing = [f for f in required if f not in d]
    print(f"  Missing fields: {missing if missing else 'NONE - all present'}")

print("\n" + "=" * 70)
print("AUDIT PROBE COMPLETE")
print("=" * 70)