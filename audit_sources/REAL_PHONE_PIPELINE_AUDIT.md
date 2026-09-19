# REAL PHONE PIPELINE AUDIT — PLAN

Goal: Fix the backend pipeline so a real phone's data flows correctly end-to-end, then verify with a real phone.

## Root cause (from prior audit, verified against live DB FK constraints)

`TrafficRepository.save_delta_sample()` only `UPDATE devices` — it never `INSERT`s. A new device (phone) whose MAC emitted traffic but that the ARP scan missed never gets a `devices` row. When `save_delta_sample` tries `INSERT INTO traffic_samples`, the FK constraint fails and the whole transaction rolls back — the phone's traffic is silently discarded and it never appears in `GET /api/devices`.

## Fixes to implement (backend only, no frontend)

1. **`network-engine/database/repository.py` — `save_delta_sample()`**: Change the `UPDATE devices` to an `INSERT ... ON CONFLICT (device_id) DO UPDATE` (upsert) so any device with real traffic is guaranteed a `devices` row with `state='ONLINE'`, `last_seen=NOW()`, and baseline counters.

2. **`network-engine/discovery/identity.py` — `get_device_id()`**: When creating a new `dev_NNN`, also `INSERT INTO devices (device_id, mac_address, state, first_seen, last_seen)` so the row exists from the moment the MAC is first seen.

3. **`network-engine/engine.py` — `discover_devices()`**: Stop flipping ONLINE devices to OFFLINE based on a single missed ARP scan. Instead, base online/offline on traffic recency (`last_seen` within `ONLINE_THRESHOLD`).

4. **`network-engine/engine.py` — `_get_device_id_by_ip()`**: Fix `connection.close()` → `return_connection(connection)` (pool leak).

5. **`network-engine/engine.py` — `_save_traffic_samples()`**: Ensure `last_seen` is updated for devices that emit no new bytes but are still ONLINE (so online status doesn't go stale).

## Verification with real phone

- Connect phone, generate traffic (YouTube, Google, Instagram, normal website, download).
- Inspect DB rows for: `devices`, `traffic_samples`, `flows`, `dns_queries`, `device_app_usage`, `device_domain_usage`, `device_category_usage`, `device_protocol_usage`, `device_activity_timeline`, `device_peaks`.
- Verify timestamps are recent, byte counters increase, speed = delta_bytes*8/elapsed, device_id stable, phone in `devices` even if ARP misses it, ONLINE/OFFLINE based on traffic recency.
- Verify DNS capture separately; distinguish domain vs DNS query vs hostname vs application vs URL/path.

## Deliverables

- REAL DATA FLOW
- ROOT CAUSE
- FILES CHANGED
- DATABASE TABLES AFFECTED
- API ENDPOINTS AFFECTED
- FRONTEND COMPONENTS AFFECTED
- REAL PHONE TEST RESULTS
- BEFORE vs AFTER
- REMAINING LIMITATIONS