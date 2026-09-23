"""Live cross-check: API payload values vs raw PostgreSQL, for every metric."""
import sys, json, urllib.request, urllib.error

sys.path.insert(0, ".")

BASE = "http://127.0.0.1:8000/api"
TOKEN = None
PAYLOAD = {}

def req(method, path, body=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}
    except Exception as e:
        return {"_error": str(e)}


def main():
    global TOKEN
    # Try known credential sets
    for user, pw in [("admin", "admin123"), ("admin", "admin"), ("root", "admin123")]:
        r = req("POST", "/auth/login", {"username": user, "password": pw})
        if "_error" not in r and "access_token" in r:
            TOKEN = r["access_token"]
            print(f"LOGGED IN as {user}")
            break
    else:
        print("LOGIN FAILED (all credential sets)")
        return

    # ---- devices ----
    devs = req("GET", "/devices/")
    print(f"\n== devices/ returned {len(devs)} items (error={devs.get('_error') if isinstance(devs, dict) else 'none'})")
    if isinstance(devs, list):
        for d in devs:
            did = d.get("device_id")
            if did and did.startswith("dev_"):
                print(f"  {did}: ip={d.get('ip')} state={d.get('state')} "
                      f"upload={d.get('upload')} download={d.get('download')} "
                      f"up_today={d.get('upload_today')} dn_today={d.get('download_today')} "
                      f"up_speed={d.get('upload_speed_bps')} dn_speed={d.get('download_speed_bps')} "
                      f"quota_used={d.get('quota_used_bytes')} quota_en={d.get('quota_enabled')} "
                      f"last_seen={d.get('last_seen')}")

    # ---- device detail ----
    for did in ["dev_002", "dev_003", "dev_006"]:
        d = req("GET", f"/devices/{did}")
        if "_error" in d and "detail" in d:
            # FastAPI detail is a string
            print(f"  /devices/{did}: error {d.get('_error')} {d.get('_body')}")
            continue
        print(f"\n  {did} detail: upload={d.get('upload')} download={d.get('download')} "
              f"up_today={d.get('upload_today')} dn_today={d.get('download_today')} "
              f"quota_used={d.get('quota_used_bytes')} quota_rem={d.get('quota_remaining_bytes')} "
              f"usage_pct={d.get('usage_percentage')}")

    # ---- analytics monthly ----
    m = req("GET", "/analytics/monthly")
    print(f"\n== analytics/monthly: {json.dumps(m, indent=1)[:800] if not isinstance(m, dict) else m}")

    m1 = req("GET", "/analytics/monthly?device_id=dev_002")
    print(f"\n== analytics/monthly dev_002: {json.dumps(m1, indent=1)[:600] if not isinstance(m1, dict) else m1}")

    # ---- analytics daily/weekly ----
    for ep in ["/analytics/daily", "/analytics/weekly", "/analytics/daily?device_id=dev_002"]:
        r = req("GET", ep)
        print(f"\n== {ep}: {json.dumps(r, indent=1)[:500] if not isinstance(r, dict) else r}")

    # ---- device intelligence ----
    for ep in [
        "/devices/dev_002/intelligence",
        "/devices/dev_002/applications",
        "/devices/dev_002/domains",
        "/devices/dev_002/categories",
        "/devices/dev_002/protocols",
        "/devices/dev_002/peaks",
        "/devices/dev_002/activity",
        "/devices/dev_002/top-applications",
        "/devices/dev_002/sni",
    ]:
        r = req("GET", ep)
        if isinstance(r, dict) and "_error" in r:
            print(f"  {ep}: HTTP {r['_error']}")
        elif isinstance(r, list):
            print(f"  {ep}: {len(r)} items, sample={json.dumps(r[:1])}")
        else:
            keys = list(r.keys()) if isinstance(r, dict) else "?"
            print(f"  {ep}: obj keys={keys}, sample={json.dumps(r)[:400] if isinstance(r, dict) else r}")

    # ---- raw DB comparison for dev_002 ----
    print("\n== RAW DB (dev_002) ==")
    from database.connection import get_connection, return_connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT total_upload, total_download, total_packets, state, last_seen
                FROM devices WHERE device_id='dev_002'
            """)
            print("devices row:", cur.fetchone())
            cur.execute("""
                SELECT day_start, download_bytes, upload_bytes, packets
                FROM usage_daily WHERE device_id='dev_002' ORDER BY day_start DESC LIMIT 5
            """)
            print("usage_daily:", cur.fetchall())
            cur.execute("""
                SELECT month_start, download_bytes, upload_bytes, packets
                FROM usage_monthly WHERE device_id='dev_002' ORDER BY month_start DESC LIMIT 3
            """)
            print("usage_monthly:", cur.fetchall())
            cur.execute("""
                SELECT COUNT(*) FROM traffic_samples WHERE device_id='dev_002'
            """)
            print("traffic_samples count:", cur.fetchone()[0])
            cur.execute("""
                SELECT download_bytes, upload_bytes, connections, download_speed_bps, upload_speed_bps, sampled_at
                FROM traffic_samples WHERE device_id='dev_002'
                ORDER BY sampled_at DESC LIMIT 1
            """)
            print("latest sample:", cur.fetchone())
            cur.execute("""
                SELECT COALESCE(SUM(download_bytes),0), COALESCE(SUM(upload_bytes),0) FROM usage_daily WHERE device_id='dev_002'
            """)
            print("usage_daily TOTAL (lifetime):", cur.fetchone())
    finally:
        return_connection(conn)


if __name__ == "__main__":
    main()