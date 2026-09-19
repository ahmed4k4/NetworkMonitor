import json, sys, time, urllib.request, urllib.error, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

B = "http://127.0.0.1:8000"

def req(m, p, b=None, t=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(B + p, data=d, method=m)
    r.add_header("Content-Type", "application/json")
    if t: r.add_header("Authorization", "Bearer %s" % t)
    try:
        with urllib.request.urlopen(r, timeout=20) as e:
            return e.status, json.loads(e.read().decode())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode())
        except: return e.code, {}
    except Exception as e:
        return 0, str(e)

ok = fail = 0
def ck(n, c, d=""):
    global ok, fail
    if c: ok += 1; print("  PASS ", n)
    else: fail += 1; print("  FAIL ", n, d)

st, r = req("POST", "/api/auth/login", {"username": "admin", "password": "admin"})
t = r.get("access_token") or r.get("token")
ck("login+token", st == 200 and bool(t), "%s %s" % (st, r))

# Find a real device
st, devs = req("GET", "/api/devices/", t=t)
ck("devices list", st == 200 and isinstance(devs, list) and len(devs) > 0, "%s" % st)
dev = devs[0]
did = dev["device_id"]
ck("device_id", bool(did), "%s" % dev)
ck("device has real mac", bool(dev.get("mac")), "%s" % dev)
ck("device has ip", bool(dev.get("ip")), "%s" % dev)

# Capture baseline
base_last_seen = dev.get("last_seen")
base_upload = dev.get("upload")
base_download = dev.get("download")

# --- RENAME (must persist) ---
test_name = "QA_Device_%d" % int(time.time())
st, r = req("POST", "/api/devices/%s/name" % did, {"name": test_name}, t)
ck("rename 200", st == 200, "%s %s" % (st, r))
st, dev2 = req("GET", "/api/devices/%s" % did, t=t)
ck("rename persisted", st == 200 and (dev2.get("custom_name") == test_name or dev2.get("hostname") == test_name), "%s" % dev2.get("custom_name"))

# --- SPEED LIMIT (limit) ---
# NOTE: endpoint treats download_limit/upload_limit as KB/s and stores bps (KB/s * 1024 * 8)
DL_KBPS = 1000
UL_KBPS = 500
EXPECTED_DL_BPS = DL_KBPS * 1024 * 8
EXPECTED_UL_BPS = UL_KBPS * 1024 * 8
st, r = req("POST", "/api/devices/%s/limit" % did, {"download_limit": DL_KBPS, "upload_limit": UL_KBPS, "enabled": True}, t)
ck("speed limit 200", st == 200, "%s %s" % (st, r))
lim_id = r.get("limit_id")
ck("speed limit id", bool(lim_id), "%s" % r)
ck("speed limit converted correctly (KB/s->bps)", r.get("download_limit_bps") == EXPECTED_DL_BPS, "got=%s want=%s" % (r.get("download_limit_bps"), EXPECTED_DL_BPS))
ck("speed limit upload converted", r.get("upload_limit_bps") == EXPECTED_UL_BPS, "got=%s want=%s" % (r.get("upload_limit_bps"), EXPECTED_UL_BPS))
st, dev3 = req("GET", "/api/devices/%s" % did, t=t)
ck("speed limit persisted", st == 200 and dev3.get("download_limit_bps") == EXPECTED_DL_BPS, "dl=%s want=%s" % (dev3.get("download_limit_bps"), EXPECTED_DL_BPS))
ck("speed limit upload persisted", dev3.get("upload_limit_bps") == EXPECTED_UL_BPS, "ul=%s want=%s" % (dev3.get("upload_limit_bps"), EXPECTED_UL_BPS))
ck("speed limit enforced fields", dev3.get("limit_enabled") is True, "en=%s" % dev3.get("limit_enabled"))
ck("speed limit db id present", dev3.get("limit_id") == lim_id or dev3.get("limit_id") is not None, "lim_id=%s db=%s" % (lim_id, dev3.get("limit_id")))

# --- DATA LIMIT (quota) ---
st, r = req("POST", "/api/devices/%s/quota" % did, {"quota_bytes": 500 * 1024 * 1024, "enabled": True}, t)
ck("data quota 200", st == 200, "%s %s" % (st, r))
qid = r.get("quota_id")
ck("data quota id", bool(qid), "%s" % r)
st, dev4 = req("GET", "/api/devices/%s" % did, t=t)
ck("data quota persisted", st == 200 and dev4.get("quota_bytes") == 500 * 1024 * 1024, "q=%s" % dev4.get("quota_bytes"))
ck("data quota enabled", dev4.get("quota_enabled") is True, "en=%s" % dev4.get("quota_enabled"))

# --- BLOCK / UNBLOCK ---
st, r = req("POST", "/api/devices/%s/block?ip=%s" % (did, dev["ip"]), None, t)
ck("block 200", st == 200, "%s %s" % (st, r))
st, r = req("POST", "/api/devices/%s/unblock" % did, None, t)
ck("unblock 200", st == 200, "%s %s" % (st, r))

print("\nCONTROLS RESULT: %d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)