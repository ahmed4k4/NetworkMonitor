"""Comprehensive LIVE verification: API (port 8000, with auth) vs DB for every metric."""
import sys, json, time, requests
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection, return_connection
from api.auth import create_access_token

BASE = "http://127.0.0.1:8000/api"
token = create_access_token('admin', 'ADMIN')
H = {"Authorization": f"Bearer {token}"}

# Wait for API to come up
up = False
for _ in range(30):
    try:
        requests.get("http://127.0.0.1:8000/", timeout=1.5)
        up = True
        break
    except Exception:
        time.sleep(1)
print("API up:", up)

def api(path, **kw):
    r = requests.get(BASE + path, headers=H, timeout=15, **kw)
    if r.status_code != 200:
        return {"__err": r.status_code, "__body": r.text[:200]}
    try:
        return r.json()
    except Exception:
        return {"__raw": r.text[:200]}

def qrows(q, args=()):
    c = get_connection()
    try:
        with c.cursor() as cur:
            cur.execute(q, args)
            return cur.fetchall()
    finally:
        return_connection(c)

def q1(q, args=()):
    rows = qrows(q, args)
    return rows[0][0] if rows else None

print("=" * 80)
print("AUDIT LIVE VERIFICATION - port 8000, auth, vs DB")
print("=" * 80)

# ---- DEVICES ----
print("\n[devices] API /devices vs DB")
api_devs = api("/devices")
db_devs = qrows("SELECT device_id, total_download, total_upload, total_packets, last_seen FROM devices ORDER BY total_download DESC LIMIT 10")
if isinstance(api_devs, list):
    print(f"  api count={len(api_devs)}, db count(rowcount)={len(db_devs)}")
    for d in api_devs[:5]:
        print(f"  {str(d.get('device_id'))[:14]:16} api_td={d.get('total_download')} api_tu={d.get('total_upload')} online={d.get('online')}")
else:
    print("  API ERR:", api_devs)
print("  DB rows:")
for r in db_devs[:5]:
    print(f"  {r[0][:14]:16} db_td={r[1]} db_tu={r[2]} db_tp={r[3]} last_seen={r[4]}")

# ---- TRAFFIC LIVE ----
print("\n[traffic] API /traffic/live vs DB traffic_samples")
tl = api("/traffic/live")
print("  /traffic/live:", json.dumps(tl)[:400] if not isinstance(tl, dict) or "__err" not in tl else tl)
try:
    rows = qrows("SELECT column_name FROM information_schema.columns WHERE table_name='traffic_samples' ORDER BY ordinal_position")
    print("  traffic_samples cols:", [r[0] for r in rows])
    latest = qrows("SELECT * FROM traffic_samples ORDER BY sampled_at DESC LIMIT 3")
    for r in latest:
        print("   DB recent:", r)
except Exception as e:
    print("  DB ERR:", e)

# ---- USAGE ----
print("\n[usage] API device usage today vs DB usage_daily")
if isinstance(api_devs, list) and api_devs:
    d0 = api_devs[0]["device_id"]
    u = api(f"/devices/{d0}/usage?days=1")
    print(f"  /devices/{d0[:14]}/usage?days=1 ->", json.dumps(u)[:300] if not isinstance(u, dict) or "__err" not in u else u)
    rows = qrows("SELECT device_id, day_start, download_bytes, upload_bytes, packets FROM usage_daily WHERE device_id=%s ORDER BY day_start DESC LIMIT 5", (d0,))
    for r in rows:
        print("   DB usage:", r)

# ---- ANALYTICS (global) ----
print("\n[analytics] global endpoints")
for ep in ["/analytics/today", "/analytics/applications", "/analytics/domains", "/analytics/domains?limit=5", "/analytics/categories", "/analytics/protocols", "/analytics/peaks"]:
    d = api(ep)
    if isinstance(d, list):
        print(f"  {ep:28} count={len(d)} first={json.dumps(d[0])[:120] if d else 'EMPTY'}")
    elif isinstance(d, dict) and "__err" not in d:
        print(f"  {ep:28} -> {json.dumps(d)[:200]}")
    else:
        print(f"  {ep:28} -> {d}")

# ---- FLOWS ----
print("\n[flows] API /flows vs DB")
fl = api("/flows")
print("  /flows:", json.dumps(fl)[:200] if not isinstance(fl, dict) or "__err" not in fl else fl)
db_flows = q1("SELECT COUNT(*) FROM flows WHERE last_seen > NOW() - INTERVAL '5 minutes'")
print("  DB flows last 5min:", db_flows)

# ---- ACTIVITY ----
print("\n[activity] API /devices/{id}/activity vs DB device_activity_timeline")
a_count = q1("SELECT COUNT(*) FROM device_activity_timeline")
print("  DB activity rows:", a_count)
if isinstance(api_devs, list) and api_devs:
    d0 = api_devs[0]["device_id"]
    act = api(f"/devices/{d0}/activity?days=7")
    print(f"  /devices/{d0[:14]}/activity?days=7 ->", json.dumps(act)[:250] if not isinstance(act, dict) or "__err" not in act else act)

# ---- PEAKS ----
print("\n[peaks] API /devices/{id}/peaks vs DB device_peaks")
p_count = q1("SELECT COUNT(*) FROM device_peaks")
print("  DB device_peaks rows:", p_count)
if isinstance(api_devs, list) and api_devs:
    d0 = api_devs[0]["device_id"]
    pk = api(f"/devices/{d0}/peaks?days=30")
    print(f"  /devices/{d0[:14]}/peaks?days=30 ->", json.dumps(pk)[:250] if not isinstance(pk, dict) or "__err" not in pk else pk)

# ---- OVERVIEW ----
print("\n[overview] endpoints")
for ep in ["/system/overview", "/system/status", "/analytics/overview", "/system/summary"]:
    d = api(ep)
    if isinstance(d, dict) and "__err" not in d:
        print(f"  {ep:24} -> {json.dumps(d)[:300]}")
    else:
        print(f"  {ep:24} -> {d}")

# ---- DNS/DOMAIN source tables ----
print("\n[dns] DB source for domains")
try:
    dns_count = q1("SELECT COUNT(*) FROM dns_queries")
    print("  db dns_queries:", dns_count)
    dns_app = q1("SELECT COUNT(*) FROM application_ids")
    print("  db application_ids:", dns_app)
except Exception as e:
    print("  DB ERR:", e)

print("\nDONE")