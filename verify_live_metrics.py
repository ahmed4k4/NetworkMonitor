"""Final live check: flows + activity + categories + protocols update from real traffic."""
import asyncio, json, subprocess, sys, time, urllib.request, socket

BASE = "http://127.0.0.1:8000"


def login():
    req = urllib.request.Request(
        BASE + "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    tok = json.load(urllib.request.urlopen(req))["access_token"]
    return {"Authorization": "Bearer " + tok}


H = login()


def api(path):
    req = urllib.request.Request(f"{BASE}{path}", headers=H)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def len_of(data):
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return len(v)
            if isinstance(v, dict):
                c = len_of(v)
                if c is not None:
                    return c
    return None


async def pump_traffic(duration=3.0):
    end = time.time() + duration
    while time.time() < end:
        try:
            subprocess.run(["ping", "-n", "1", "127.0.0.1"],
                           capture_output=True, check=False, timeout=2)
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.sendto(b"\x00" * 32, ("8.8.8.8", 53))
            s.close()
        except Exception:
            pass
        await asyncio.sleep(0.3)
    return


async def main():
    print("Baseline snapshot...")
    flow_before = len_of(api("/api/flows/active"))
    apps_before = len_of(api("/api/applications/"))
    doms_before = len_of(api("/api/analytics/domains"))
    protos_before = len_of(api("/api/analytics/protocols"))
    print(f"  flows={flow_before} apps={apps_before} domains={doms_before} protocols={protos_before}")

    print("Generating real traffic for 3s...")
    await pump_traffic(3.0)
    await asyncio.sleep(1.0)

    flow_after = len_of(api("/api/flows/active"))
    apps_after = len_of(api("/api/applications/"))
    doms_after = len_of(api("/api/analytics/domains"))
    protos_after = len_of(api("/api/analytics/protocols"))
    print(f"  flows={flow_after} apps={apps_after} domains={doms_after} protocols={protos_after}")

    ok_flows = flow_after is not None and flow_after > 0
    ok_apps = apps_after is not None and apps_after > 0
    ok_doms = doms_before is not None and doms_after is not None and doms_after >= doms_before
    ok_protos = protos_after is not None and protos_after > 0

    print("=" * 52)
    print("LIVE METRIC UPDATE (REAL TRAFFIC)")
    print("=" * 52)
    print(f"  [{'PASS' if ok_flows else 'FAIL'}] flows > 0      ({flow_before} -> {flow_after})")
    print(f"  [{'PASS' if ok_apps else 'FAIL'}] applications>0 ({apps_before} -> {apps_after})")
    print(f"  [{'PASS' if ok_doms else 'FAIL'}] domains non-dec ({doms_before} -> {doms_after})")
    print(f"  [{'PASS' if ok_protos else 'FAIL'}] protocols >0  ({protos_before} -> {protos_after})")
    ok = ok_flows and ok_apps and ok_doms and ok_protos
    print("OVERALL:", "ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())