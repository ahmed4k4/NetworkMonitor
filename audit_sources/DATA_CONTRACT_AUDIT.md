# COMPLETE DATA CONTRACT AUDIT — network-monitor (CORRECTED)

Audit date: 2026-08-31 (UTC+3)
Scope: physical network → packet capture → engine → discovery → flow → DNS → attribution → aggregation → PostgreSQL → API → WebSocket → Next.js → Device Page.
No code modified. Findings below are from source inspection + live schema probe (FK constraints verified against the running DB).

> **CORRECTION vs. prior audit (2026-08-28):** The prior audit claimed "orphan traffic_samples" and that `save_delta_sample`'s `INSERT INTO traffic_samples` succeeds while the `UPDATE devices` is a no-op. **This is incorrect.** The live DB shows `traffic_samples.device_id` has a hard `FOREIGN KEY → devices.device_id`. For a new device with no `devices` row, the `INSERT INTO traffic_samples` **fails with a FK violation**, and because the whole method is one `try/except` that rolls back on any error, **the entire sample (traffic_samples + usage_* + devices totals + last_seen) is silently dropped**. There are zero orphans because the FK rejects the write outright.

---

## DATA CONTRACT TABLE (verified, no mock/random anywhere in the data path)

| SOURCE | DB TABLE | API ENDPOINT | FRONTEND HOOK/QUERY | FRONTEND COMPONENT |
|---|---|---|---|---|
| ARP scan (`discovery/scanner.py` → `engine.discover_devices`) | `devices` (INSERT only via `upsert_device`) | `GET /api/devices` | `api.getDevices()` (`dashboard/lib/api.ts`) | `dashboard/app/devices/page.tsx` |
| Packets (`capture/sniffer.py` → `engine.process_packet`) | `flows`, `traffic_samples`, `usage_daily/hourly/monthly`, `data_limits` | `GET /api/devices` (LATERAL speed), WS `traffic_update` | `useWebSocket` → `handleMessage` | `devices/page.tsx`, `devices/[id]/page.tsx` |
| `engine._save_traffic_samples` (real byte deltas) | `traffic_samples` (`sampled_at`, `download_speed_bps`, `upload_speed_bps`), `usage_*`, `devices.total_*`, `devices.last_seen` | `GET /api/devices` | REST bootstrap + WS | `devices/page.tsx` |
| Flow attribution (`_attribute_and_save_flow`) | `device_app_usage`, `device_domain_usage`, `device_protocol_usage`, `device_category_usage`, `device_peaks`, `device_activity_timeline` | `GET /api/devices/{id}/applications`, `/domains`, `/categories`, `/protocols`, `/peaks`, `/activity` | `api.getDeviceApplications/Domains/Categories/Protocols/Peaks/Activity` | `devices/[id]/page.tsx` |
| DNS (`intel_repo.save_dns_query`) | `dns_queries` | `GET /api/dns` | dns pages | dns pages |
| Live traffic samples | `traffic_samples` | `GET /api/traffic/recent?device_id=` | `api.getDeviceTraffic` | `devices/[id]/page.tsx` (Live Traffic chart) |
| Traffic history | `traffic_samples` (NOT `usage_daily` — see note) | `GET /api/traffic/history?device_id=&days=` | `api.getDeviceTrafficHistory` | `devices/[id]/page.tsx` (Traffic History chart) |

**No `mock`, `dummy`, `sample`, `demo`, `fake`, `Math.random` numeric data, hardcoded stats, or seed traffic was found in any writer, repository, API, or the devices page.** Every displayed number traces to captured traffic (or a cleared historical row). The only `Math.random` usages are in `dashboard/lib/websocket.ts` for reconnect jitter and request IDs — not data.

---

## METRIC VERDICTS

| Metric | Verified? | Notes |
|---|---|---|
| device online/offline | ✗ BROKEN | Determined by ARP presence, NOT by traffic recency (see root cause). A device that emits traffic but is missed by one 10s ARP scan is marked OFFLINE. |
| upload bytes / download bytes | ✅ real | `traffic_samples` deltas accumulate into `devices.total_upload/download` + `usage_daily` — **but only for devices that already have a `devices` row**. |
| upload speed / download speed | ✅ real | `speed = delta_bytes * 8 / elapsed` in `engine._save_traffic_samples`; real `download_speed_bps`/`upload_speed_bps` columns. |
| total traffic | ✅ real | `usage_daily` (today), `devices.total_*` (all-time) — **only for devices with a `devices` row**. |
| applications | ✅ real | `_attribute_and_save_flow` increments app usage from actual flow bytes. |
| domains | ✅ real | DNS query + flow correlation (device_id + response_ip + time window). |
| protocols/categories | ✅ real | incremented from actual attributed flow bytes. |
| activity timeline | ✅ real | `save_activity_timeline` hour-start from `flow.started_at`. |
| peak usage | ✅ real | `save_peak` from `delta_bytes*8/duration`. |
| last seen | ⚠️ partial | Updated to `NOW()` by `save_delta_sample`; but a device that emits no new bytes for a cycle has `last_seen` NOT updated. **Critical: a device row that is never created has no `last_seen` at all.** |
| packet count | ✅ real | `packets_delta` into `traffic_samples`/`devices.total_packets`. |
| flow count | ✅ real | flow manager ACTIVE count. |
| units (bytes vs bits) | ✅ correct | Engine stores bytes; speeds in bps. Frontend `formatBytes` uses 1024 (bytes); `formatSpeed` uses 1e6/1e3 (bps→Mbps/Kbps). No cross-conversion. |
| speed formula | ✅ correct | `speed_bps = delta_bytes * 8 / elapsed_seconds`; never derives speed from cumulative totals. |
| timestamps/timezone | ✅ consistent | Writer and API both bucket `usage_daily`/history with `Africa/Cairo` (`APP_TZ`); `traffic_samples`/`device_peaks` are `timestamptz`. No UTC/APP drift. |

---

## NEW PHONE TRACE (where it disappears — CORRECTED)

1. Phone joins LAN, gets DHCP IP, sends traffic.
2. `engine.process_packet` sees LAN MAC → `_get_device_id_by_mac` → `DeviceIdentityManager.get_device_id(mac)` → **creates `dev_NNN` in memory only** (no `devices` row inserted).
3. `device_bytes[dev_NNN]` accumulates real deltas.
4. `_save_traffic_samples` → `TrafficRepository.save_delta_sample(dev_NNN, ...)`:
   - `INSERT INTO traffic_samples` → **FK VIOLATION** (`traffic_samples.device_id REFERENCES devices(device_id)`, and no `devices` row exists for `dev_NNN`).
   - The single `try/except` catches the exception, logs `Error saving delta traffic sample: {e}`, and **rolls back the ENTIRE transaction**.
   - Result: NO `traffic_samples`, NO `usage_daily/hourly/monthly`, NO `devices.total_*`, NO `last_seen` update. **The phone's traffic is completely lost.**
5. `GET /api/devices` does `FROM devices` → the phone has no `devices` row → **NOT LISTED AT ALL**.
6. If the ARP scanner happens to see the phone, it `upsert_device`s a row — but then the same `discover_devices()` loop marks it `OFFLINE` whenever the next scan (10s interval) misses it (AP isolation / phone sleep / ARP probe no-reply).

**Exact broken stage: Traffic sampler → devices table (row creation contract). The phone disappears at the `INSERT INTO traffic_samples` FK violation, which silently drops the entire sample.**

---

## FINAL REPORT (CORRECTED)

1. **Broken stage:** Traffic sampler → devices table (row creation contract). Secondary broken stage: online/offline decision.
2. **Root cause:** `save_delta_sample()` (and `update_device_usage()`) assume a `devices` row already exists and only `UPDATE` — they never `INSERT`. The row is created only by the ARP-scan `upsert_device`. A device whose MAC emitted traffic but that the periodic ARP broadcast probe did not answer never gets a `devices` row. When `save_delta_sample` tries to `INSERT INTO traffic_samples` for that device, the **FK constraint fails**, and the whole transaction is rolled back — so the device's traffic is silently discarded and it never appears in `GET /api/devices`. Concurrently, `discover_devices()` marks any existing ONLINE device `OFFLINE` whenever one 10s ARP scan misses it, regardless of recent real traffic → "appears offline".
3. **File:** `network-engine/database/repository.py`
4. **Function:** `TrafficRepository.save_delta_sample()` (lines 598-721) — `INSERT INTO traffic_samples` fails on FK; whole method rolls back. Related: `DeviceRepository.update_device_usage()`, `NetworkEngine.discover_devices()` offline-marking, `DeviceIdentityManager.get_device_id()` (creates in-memory id but never inserts a `devices` row).
5. **Database table:** `devices` (missing row) + `traffic_samples`/`usage_*` (FK-rejected writes). FK constraints verified live: `traffic_samples`, `usage_daily`, `usage_hourly`, `usage_monthly`, `flows`, `dns_queries`, `device_app_usage`, `device_domain_usage`, `device_category_usage`, `device_protocol_usage`, `device_peaks`, `device_activity_timeline`, `sni_observations`, `connections`, `data_limits`, `speed_limits`, `firewall_rules`, `network_rules`, `alerts`, `audit_logs`, `events` — ALL `FOREIGN KEY device_id → devices.device_id`.
6. **API endpoint:** `GET /api/devices` (`network-engine/api/routes/devices.py` `get_devices`) — `FROM devices` LEFT JOIN, so a device with no `devices` row is never returned.
7. **Frontend component:** `dashboard/app/devices/page.tsx` (`DevicesPage`) — shows only what the API returns; new phone absent, or offline tag from `device_offline` WS.
8. **Exact fix required (NOT yet applied):**
   - **Primary fix:** In `save_delta_sample()`, before the `INSERT INTO traffic_samples`, ensure a `devices` row exists. Best approach: change the `UPDATE devices` to an `INSERT ... ON CONFLICT (device_id) DO UPDATE` (upsert) so any device with real traffic is guaranteed a `devices` row with `state='ONLINE'`, `last_seen=NOW()`, and baseline counters. The `device_id` is already known; MAC/IP/hostname can be captured at flow time or fetched by device_id.
   - **Alternative/defense-in-depth:** In `DeviceIdentityManager.get_device_id()`, when creating a new `dev_NNN`, also `INSERT INTO devices (device_id, mac_address, state, first_seen, last_seen) VALUES (...)` so the row exists from the moment the MAC is first seen.
   - **Online/offline fix:** Recompute online status from traffic recency, not ARP presence. Define `ONLINE_THRESHOLD` (e.g. `last_seen` within 60s = ONLINE), derive status in the API/frontend from `last_seen`, and stop `discover_devices()` from flipping to OFFLINE based solely on a single missed ARP scan.
   - **Minor bug:** `engine._get_device_id_by_ip` (line 356) uses `connection.close()` instead of `return_connection()` — leaks the pooled connection. Fix to `return_connection(connection)`.

System is NOT yet fixed; only the broken stage is identified with source + live-DB evidence.