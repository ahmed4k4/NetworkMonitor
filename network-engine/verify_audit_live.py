"""Final consolidated LIVE verification: DB records vs API responses for every metric."""
import json, urllib.request
from datetime import datetime, timedelta, timezone
from database.connection import get_connection, return_connection

BASE = "http://127.0.0.1:8080"
APP_TZ = "Africa/Cairo"

def api(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return json.loads(r.read().decode())

def db(q, args=()):
    c = get_connection()
    try:
        with c.cursor() as cur:
            cur.execute(q, args)
            return cur.fetchall()
    finally:
        return_connection(c)

def q1(q, args=()):
    rows = db(q, args)
    return rows[0][0] if rows else None

print("=" * 78)
print(f"LIVE DATA FLOW VERIFICATION  {datetime.now(timezone.utc).astimezone().isoformat()}")
print("=" * 78)

# ---- 1. devices: totals vs traffic_samples vs usage_daily ----
print("\n[1] DEVICE persist totals  (devices.total_* / traffic_samples / usage_daily)")
rows = db("""
    SELECT d.device_id, d.total_upload, d.total_download, d.total_packets, d.last_seen,
           (SELECT COALESCE(SUM(download_bytes),0) FROM traffic_samples t WHERE t.device_id=d.device_id) sum_dl,
           (SELECT COALESCE(SUM(upload_bytes),0)   FROM traffic_samples t WHERE t.device_id=d.device_id) sum_ul,
           (SELECT COALESCE(SUM(download_bytes),0) FROM usage_daily u WHERE u.device_id=d.device_id AND u.day_start=(NOW() AT TIME ZONE %s)::date) today_dl,
           (SELECT COALESCE(SUM(upload_bytes),0)   FROM usage_daily u WHERE u.device_id=d.device_id AND u.day_start=(NOW() AT TIME ZONE %s)::date) today_ul
    FROM devices d ORDER BY d.total_download DESC LIMIT 8
""", (APP_TZ, APP_TZ))
for r in rows:
    print(f"  {r[0][:14]:14} total_dl={r[1]:>12} total_ul={r[2]:>12} sum_ts_dl={r[5]:>12} sum_ts_ul={r[6]:>12} today_dl={r[7]:>10} today_ul={r[8]:>10} last_seen={r[4]}")

# ---- 2. API /devices ----
print("\n[2] API GET /devices  (device card totals)")
try:
    devs = api("/devices")
    print(f"  count={len(devs)}")
    for d in devs[:8]:
        u = d.get("total_upload"); dl = d.get("total_download")
        print(f"  {str(d.get('device_id'))[:14]:14} api_total_upload={u} api_total_download={dl} online={d.get('online')} state={d.get('state')}")
except Exception as e:
    print("  API ERROR:", e)

# ---- 3. Device usage today API ----
print("\n[3] API /devices/{id}/usage  (today bytes per device)")
try:
    for d in devs[:4]:
        did = d["device_id"]
        try:
            u = api(f"/devices/{did}/usage?days=1")
            today = u[0] if isinstance(u, list) and u else u
            print(f"  {did[:14]:14} -> {json.dumps(today)[:160] if today else 'EMPTY'}")
        except Exception as e:
            print(f"  {did[:14]:14} -> ERR {e}")
except Exception as e:
    print("  ERR", e)

# ---- 4. Usage today vs DB ----
print("\n[4] GET /api usage/today vs DB usage_daily")
try:
    t = api("/usage/today")
    print("  api /usage/today:", json.dumps(t)[:300])
except Exception as e:
    print("  /usage/today ERR", e)
try:
    t2 = api("/traffic/today")
    print("  api /traffic/today:", json.dumps(t2)[:300])
except Exception:
    pass
print("  DB usage_daily today sum:", q1("SELECT COALESCE(SUM(download_bytes),0), COALESCE(SUM(upload_bytes),0) FROM usage_daily WHERE day_start=(NOW() AT TIME ZONE %s)::date", (APP_TZ,)))

# ---- 5. Live traffic endpoint (real last N samples) ----
print("\n[5] API /traffic/live  (top combined rows)")
try:
    live = api("/traffic/live")
    print(f"  rows={len(live) if isinstance(live,list) else live}")
    if isinstance(live, list):
        for s in live[:5]:
            print("   ", json.dumps(s)[:200])
except Exception as e:
    print("  ERR", e)

# ---- 6. Peaks ----
print("\n[6] device_peaks row count vs API /devices/{id}/peaks")
print("  DB device_peaks rows:", q1("SELECT COUNT(*) FROM device_peaks"))
try:
    for d in devs[:3]:
        did = d["device_id"]
        try:
            pk = api(f"/devices/{did}/peaks?days=30")
            n = len(pk) if isinstance(pk, list) else pk
            print(f"  {did[:14]:14} api peaks -> {json.dumps(pk)[:180] if isinstance(pk,list) else pk}")
        except Exception as e:
            print(f"  {did[:14]:14} peaks ERR {e}")
except Exception as e:
    print("  ERR", e)

# ---- 7. Activity timeline ----
print("\n[7] device_activity_timeline count vs API")
print("  DB activity rows:", q1("SELECT COUNT(*) FROM device_activity_timeline"))
try:
    for d in devs[:2]:
        did = d["device_id"]
        try:
            a = api(f"/devices/{did}/activity?days=7")
            print(f"  {did[:14]:14} api activity -> {json.dumps(a)[:200] if isinstance(a,list) else a}")
        except Exception as e:
            print(f"  {did[:14]:14} activity ERR {e}")
except Exception as e:
    print("  ERR", e)

# ---- 8. Flow / connections ----
print("\n[8] flows & connections live")
try:
    fl = api("/flows")
    print(f"  /flows rows={len(fl) if isinstance(fl,list) else fl}")
except Exception as e:
    print("  /flows ERR", e)
print("  DB latest flows:", q1("SELECT COUNT(*) FROM flows WHERE end_time > NOW() - INTERVAL '5 minutes'"))

print("\nDONE")