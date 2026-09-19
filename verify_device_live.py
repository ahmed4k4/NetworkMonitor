import sys, io, json, urllib.request, urllib.error, time, subprocess, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
B = "http://127.0.0.1:8000"

def req(m, p, b=None, t=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(B + p, data=d, method=m)
    r.add_header("Content-Type", "application/json")
    if t: r.add_header("Authorization", "Bearer %s" % t)
    try:
        with urllib.request.urlopen(r, timeout=15) as e:
            return e.status, json.loads(e.read().decode())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode())
        except: return e.code, {}
    except Exception as e:
        return 0, str(e)

print("="*70); print("LIVE DEVICE VERIFICATION - REAL TRAFFIC PIPELINE"); print("="*70)

st, r = req("POST", "/api/auth/login", {"username": "admin", "password": "admin"})
t = r.get("access_token") or r.get("token")
print("login:", st, "token:", bool(t))
if not t: sys.exit(1)

# capture config
import importlib.util
spec = importlib.util.spec_from_file_location("ncfg", os.path.join("network-engine", "config.py"))
ncfg = importlib.util.module_from_spec(spec); spec.loader.exec_module(ncfg)
cfg = ncfg.network_config
print("lan_ip:", getattr(cfg,"lan_ip","?"), "| lan_subnet:", getattr(cfg,"lan_subnet",None),
      "| iface:", getattr(cfg,"lan_interface","?"), "| gw:", getattr(cfg,"upstream_gateway","?"),
      "| disc_interval:", getattr(cfg,"discovery_interval","?"))

st, before = req("GET", "/api/devices/", t=t)
print("\nDevices BEFORE:", st, "count:", len(before) if isinstance(before,list) else before)
targets = [d for d in (before if isinstance(before,list) else []) if d.get("state")=="ONLINE"] or (before if isinstance(before,list) else [])
for d in targets:
    print("  ", d.get("device_id"), d.get("mac"), d.get("ip"), d.get("state"),
          "last_seen:", d.get("last_seen"), "up:", d.get("upload"), "down:", d.get("download"))

print("\n--- Generating real traffic (ping device IPs) ---")
for d in targets:
    ip = d.get("ip")
    if not ip: continue
    print("pinging", ip)
    try:
        r0 = subprocess.run(["ping","-n","3","-w","1000",str(ip)], capture_output=True, text=True, timeout=12)
        print("   rc:", r0.returncode)
    except Exception as e:
        print("   err:", e)

gw = getattr(cfg,"upstream_gateway",None) or getattr(cfg,"lan_ip",None)
if gw:
    print("pinging gateway", gw)
    try:
        r1 = subprocess.run(["ping","-n","3","-w","1000",str(gw)], capture_output=True, text=True, timeout=12)
        print("   rc:", r1.returncode)
    except Exception as e:
        print("   err:", e)

print("\nWaiting 70s for discovery + sample loop...")
time.sleep(70)

st, after = req("GET", "/api/devices/", t=t)
print("\nDevices AFTER:", st, "count:", len(after) if isinstance(after,list) else after)
for d in (after if isinstance(after,list) else []):
    print("  ", d.get("device_id"), d.get("mac"), d.get("ip"), d.get("state"),
          "last_seen:", d.get("last_seen"), "up:", d.get("upload"), "down:", d.get("download"),
          "dl_speed:", d.get("download_speed_bps"), "ul_speed:", d.get("upload_speed_bps"),
          "pkts:", d.get("total_packets"))

# Also check flows for the online device after traffic
for d in (after if isinstance(after,list) else []):
    if not d.get("device_id"): continue
    stf, flows = req("GET", "/api/devices/%s/flows?limit=5" % d["device_id"], t=t)
    print("\nFlows for", d["device_id"], "status", stf, "count:", len(flows) if isinstance(flows,list) else flows)
    if isinstance(flows, list):
        for f in flows[:3]:
            print("   ", f.get("source_ip"), "->", f.get("destination_ip"), f.get("protocol"), f.get("bytes"))

print("\n--- done ---")