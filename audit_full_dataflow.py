import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")

from config import database_config
import psycopg

B = "http://127.0.0.1:8000"

R = {}

def api(path, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(B + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, str(e.read())

# ---- Login with debug ----
login_st, login_body = api("/api/auth/login", "POST", {"username": "admin", "password": "admin"})
R["login_status"] = login_st
R["login_keys"] = list(login_body.keys()) if isinstance(login_body, dict) else type(login_body).__name__ + ":" + str(login_body)[:200]
token = None
if isinstance(login_body, dict):
    token = login_body.get("access_token") or login_body.get("token") or login_body.get("data", {}).get("access_token") if isinstance(login_body.get("data"), dict) else login_body.get("access_token")
R["token_found"] = bool(token)

conn = psycopg.connect(host=database_config.host, port=database_config.port,
                       dbname=database_config.database, user=database_config.user,
                       password=database_config.password,
                       autocommit=True)
cur = conn.cursor()

def q(sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()

R["tables"] = [(r[0].lower(), r[1], r[2]) for r in q(
    "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position")]

# ---- Devices from API vs DB ----
st, dev_api_body = api("/api/devices/", token=token)
R["dev_api_status"] = st
dev_api = dev_api_body
if isinstance(dev_api, dict):
    R["dev_api_error"] = json.dumps(dev_api)[:400]
    dev_api = []
R["dev_api_count"] = len(dev_api)
db_dev = {r[0]: r for r in q(
    "SELECT device_id, total_upload, total_download, total_packets, last_seen, state FROM devices")}
R["dev_db_count"] = len(db_dev)

R["devices"] = []
for d in dev_api:
    row = db_dev.get(d["device_id"])
    R["devices"].append({
        "device_id": d["device_id"], "state": d["state"],
        "api_upload": d["upload"], "db_upload": row[1] if row else None,
        "api_download": d["download"], "db_download": row[2] if row else None,
        "upload_match": (row and d["upload"] == row[1]),
        "download_match": (row and d["download"] == row[2]),
        "db_packets": row[3] if row else None,
        "db_last_seen": str(row[4]) if row else None,
        "api_last_seen": d["last_seen"],
        "upload_today": d["upload_today"], "download_today": d["download_today"],
        "up_speed": d["upload_speed_bps"], "down_speed": d["download_speed_bps"],
        "quota_bytes": d["quota_bytes"], "quota_enabled": d["quota_enabled"],
    })

# ---- usage_daily today (Cairo) vs API today ----
try:
    usage_agg = q(
        "SELECT device_id, SUM(upload_bytes), SUM(download_bytes) FROM usage_daily "
        "WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date GROUP BY device_id")
    usage_map = {r[0]: (r[1] or 0, r[2] or 0) for r in usage_agg}
    R["today_match"] = []
    for d in dev_api:
        u = usage_map.get(d["device_id"], (0, 0))
        R["today_match"].append({
            "device_id": d["device_id"],
            "api_up_today": d["upload_today"], "db_up_today": u[0],
            "api_down_today": d["download_today"], "db_down_today": u[1],
            "ok": d["upload_today"] == u[0] and d["download_today"] == u[1],
        })
except Exception as e:
    R["today_err"] = str(e)

# ---- traffic_samples latest speed vs API speed ----
try:
    samp = q(
        "SELECT device_id, upload_speed_bps, download_speed_bps FROM traffic_samples s "
        "WHERE sampled_at = (SELECT MAX(sampled_at) FROM traffic_samples s2 WHERE s2.device_id=s.device_id) "
        "ORDER BY device_id")
    samp_map = {r[0]: (r[1], r[2]) for r in samp}
    R["speed_match"] = []
    for d in dev_api:
        s = samp_map.get(d["device_id"])
        R["speed_match"].append({
            "device_id": d["device_id"],
            "api_up_speed": d["upload_speed_bps"], "db_up_speed": s[0] if s else None,
            "api_down_speed": d["download_speed_bps"], "db_down_speed": s[1] if s else None,
            "no_sample": s is None,
        })
except Exception as e:
    R["speed_err"] = str(e)

# ---- Device detail + history ----
st, detail = api("/api/devices/dev_002", token=token)
R["detail_status"] = st
if isinstance(detail, dict) and "detail" in detail and st == 401:
    R["detail_auth"] = detail
else:
    R["detail_keys"] = sorted(detail.keys()) if isinstance(detail, dict) else type(detail).__name__
    R["history_len"] = len(detail.get("history", [])) if isinstance(detail, dict) else None
    R["history_sample"] = (detail.get("history") or [])[:3] if isinstance(detail, dict) else None

# ---- Intelligence endpoints for real device ----
def intel(path):
    st, data = api(path, token=token)
    if st != 200:
        return {"status": st, "detail": data}
    if isinstance(data, dict) and not isinstance(data.get("applications"), list) and not isinstance(data.get("domains"), list)\
       and not isinstance(data.get("categories"), list) and not isinstance(data.get("protocols"), list):
        return {"status": st, "type": type(data).__name__, "keys": list(data.keys())[:20], "preview": json.dumps(data)[:600]}
    return {"status": st, "len": len(data) if isinstance(data, list) else None,
            "first": data[0] if isinstance(data, list) and data else data}

R["intel"] = {}
for path in ["/api/devices/dev_002/intelligence?range=24h",
             "/api/devices/dev_002/applications?range=24h",
             "/api/devices/dev_002/domains?range=24h&limit=20",
             "/api/devices/dev_002/categories?range=24h",
             "/api/devices/dev_002/protocols?range=24h",
             "/api/devices/dev_002/top-applications?range=24h&limit=5",
             "/api/devices/dev_002/peaks?days=7",
             "/api/devices/dev_002/activity?days=1",
             "/api/devices/dev_002/sni?range=24h"]:
    name = path.split("/")[-1].split("?")[0]
    R["intel"][name] = intel(path)

# ---- Raw tables counts ----
for t in ["dns_queries", "flows", "traffic_samples", "usage_daily", "usage_monthly", "usage_weekly", "peak_usage"]:
    try:
        n = q(f"SELECT COUNT(*) FROM {t}")[0][0]
        R[f"count_{t}"] = n
    except Exception as e:
        R[f"count_{t}"] = f"ERR {e}"

# ---- flows for dev_002 ----
try:
    n = q("SELECT COUNT(*) FROM flows WHERE device_id='dev_002'")[0][0]
    R["flows_dev002"] = n
except Exception as e:
    R["flows_dev002"] = f"ERR {e}"
try:
    cols = [r[1] for r in q("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='flows' ORDER BY ordinal_position")]
    R["flows_cols"] = cols
    sample = q("SELECT * FROM flows WHERE device_id='dev_002' LIMIT 1")
    R["flows_sample"] = [str(r) for r in sample]
except Exception as e:
    R["flows_sample"] = f"ERR {e}"

# ---- Analytics table column names ----
for t in ["traffic_samples", "usage_daily", "usage_monthly", "usage_weekly", "peak_usage"]:
    try:
        cols = [r[1] for r in q("SELECT column_name FROM information_schema.columns "
                             "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (t,))]
        R[f"cols_{t}"] = cols
    except Exception as e:
        R[f"cols_{t}"] = f"ERR {e}"

conn.close()
print(json.dumps(R, indent=1, default=str))