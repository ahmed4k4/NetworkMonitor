"""LIVE WebSocket end-to-end proof. Simulates engine's asyncio_safe_broadcast POST."""
import asyncio, json, sys, time, urllib.request
import websockets

BASE = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000/ws"
TAG = "e2e-ws-live"


def post(t, d):
    req = urllib.request.Request(f"{BASE}/api/system/broadcast",
        data=json.dumps({"type": t, "data": d}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status


async def next_json(ws, timeout=1.5):
    """Read next JSON message from ws (skipping blanks/non-json)."""
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            if raw is None:
                continue
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                continue
        except asyncio.TimeoutError:
            return None


async def wait_for(ws, msg_type, key, val, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        m = await next_json(ws)
        if m is None:
            continue
        if m.get("type") == msg_type and m.get("data", {}).get(key) == val:
            return m
    return None


async def main():
    results = []
    async with websockets.connect(WS, open_timeout=10) as ws:
        welcome = await next_json(ws, 5)
        results.append(("welcome", bool(welcome and welcome.get("type") == "connected")))

        await ws.send(json.dumps({"type": "subscribe",
            "data": {"topics": ["traffic_update", "device_online", "device_offline"]}}))
        ack = await wait_for(ws, "subscribed", "topics", ["traffic_update", "device_online", "device_offline"])

        # Subscribe ack: check type only (topics list may be wrapped/incomplete)
        if ack is None:
            results.append(("subscribed_ack", False))
        else:
            results.append(("subscribed_ack", ack.get("type") == "subscribed"))

        s = post("traffic_update", {"device_id": TAG, "download_speed_bps": 123456,
                                    "upload_speed_bps": 65432, "timestamp": time.time()})
        results.append(("broadcast_post_200", s == 200))
        got = await wait_for(ws, "traffic_update", "device_id", TAG)
        results.append(("traffic_update_received", got is not None))

        post("device_online", {"device_id": TAG, "ip": "10.0.0.250"})
        got_online = await wait_for(ws, "device_online", "device_id", TAG)
        results.append(("device_online_received", got_online is not None))

        post("device_offline", {"device_id": TAG})
        got_off = await wait_for(ws, "device_offline", "device_id", TAG)
        results.append(("device_offline_received", got_off is not None))

    print("=" * 52)
    print("WEBSOCKET LIVE END-TO-END")
    print("=" * 52)
    all_ok = True
    for name, ok in results:
        if not ok:
            all_ok = False
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 52)
    print("OVERALL:", "ALL PASS" if all_ok else "SOME FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
