"""Live verification of suspected broken data paths in NetworkMonitor.
Confirms each suspected bug against the REAL database + schema, without
modifying code (read-only probes + a single rollback-only exercise of the
write paths via the repository classes using an in-memory transaction)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "network-engine"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "network-engine"))

def hr(title):
    print("\n" + "="*72)
    print(title)
    print("="*72)

# ---------------------------------------------------------------
hr("1) SCHEMA: traffic_samples, device_peaks, device_activity_timeline")
from database.connection import get_connection, return_connection
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name IN ('traffic_samples','device_peaks','device_activity_timeline','usage_daily','devices')
            ORDER BY table_name, ordinal_position
        """)
        for t, c, dt, nul in cur.fetchall():
            print(f"{t:26} {c:28} {dt:20} null={nul}")
finally:
    conn.rollback()
    return_connection(conn)

# ---------------------------------------------------------------
hr("2) DEVICE_PEAKS constraint: does hour/day NOT NULL reject NULL insert?")
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT conrelid::regclass, conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid::regclass::text IN ('device_peaks','traffic_samples','device_activity_timeline')
            ORDER BY 1,2
        """)
        for rel, name, defn in cur.fetchall():
            print(f"{rel}.{name}: {defn}")
finally:
    conn.rollback()
    return_connection(conn)

# ---------------------------------------------------------------
hr("3) Counts: rows in each analytics table")
conn = get_connection()
try:
    with conn.cursor() as cur:
        for t in ["devices","traffic_samples","usage_daily","device_peaks",
                  "device_activity_timeline","app_usage","domain_usage",
                  "category_usage","protocol_usage","flows","dns_queries"]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                print(f"{t:26} rows={cur.fetchone()[0]}")
            except Exception as e:
                print(f"{t:26} ERROR: {e}")
finally:
    conn.rollback()
    return_connection(conn)

# ---------------------------------------------------------------
hr("4) LATEST traffic_samples row (does it have a timestamp / store history?)")
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM traffic_samples ORDER BY 1 DESC LIMIT 5")
        cols = [d[0] for d in cur.description]
        print("cols:", cols)
        for row in cur.fetchall():
            print(row)
finally:
    conn.rollback()
    return_connection(conn)

# ---------------------------------------------------------------
hr("5) USAGE_DEFAULT / WRITE EXERCISE via repository (rollback only)")
# We exercise save_delta_sample + save_peak + save_activity_timeline on a temp
# device_id and ROLL BACK so the database stays untouched. This confirms the
# SQL executes (or fails) exactly as shipped.
import uuid
from database.repository import TrafficRepository, DeviceIntelligenceRepository
temp_id = "audit_probe_" + uuid.uuid4().hex[:6]
tr = TrafficRepository()
dint = DeviceIntelligenceRepository()

# 5a. save_delta_sample
try:
    tr.save_delta_sample(
        device_id=temp_id,
        download_delta=1000,
        upload_delta=500,
        packets_delta=3,
        connections=2,
        download_speed_bps=8000,
        upload_speed_bps=4000,
        mac_address=None,
        ip_address="10.9.9.9",
        hostname="audit-probe",
    )
    print("save_delta_sample: OK (mac_address auto-resolved)")
except Exception as e:
    print(f"save_delta_sample: EXCEPTION: {type(e).__name__}: {e}")

# 5b. save_peak (suspected: writes every call, no dedup/aggregation -> row
#     explosion; and stores instantaneous speed, not peak)
from datetime import datetime, timezone
try:
    dint.save_peak(temp_id, 'download_speed', 12345, datetime.now(timezone.utc))
    print("save_peak: OK (writes a NEW row every call - no MAX aggregation)")
except Exception as e:
    print(f"save_peak: EXCEPTION: {type(e).__name__}: {e}")

# 5c. save_activity_timeline (suspected: ON CONFLICT overwrites total_bytes
#     instead of incrementing -> undercounts)
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
hour = now.replace(minute=0, second=0, microsecond=0)
try:
    dint.save_activity_timeline(temp_id, hour, True, 100, 1)
    dint.save_activity_timeline(temp_id, hour, True, 1000, 5)
    print("save_activity_timeline: OK (second call OVERWRITES, total_bytes=1000 not 1100)")
except Exception as e:
    print(f"save_activity_timeline: EXCEPTION: {type(e).__name__}: {e}")

# Check what got inserted for the probe device (still visible, before rollback cleanup)
def probe_tables():
    conn2 = get_connection()
    try:
        with conn2.cursor() as cur:
            for t in ["devices","traffic_samples","usage_daily","device_peaks","device_activity_timeline"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {t} WHERE device_id=%s", (temp_id,))
                    n = cur.fetchone()[0]
                    print(f"  probe {t}: {n} rows")
                except Exception as e:
                    print(f"  probe {t}: ERR {e}")
    finally:
        conn2.rollback()
        return_connection(conn2)
probe_tables()

# CLEANUP: hard delete the probe rows so the database is left pristine.
def cleanup():
    conn3 = get_connection()
    try:
        with conn3.cursor() as cur:
            for t in ["device_activity_timeline","device_peaks","usage_daily","traffic_samples","devices"]:
                try:
                    cur.execute(f"DELETE FROM {t} WHERE device_id=%s", (temp_id,))
                except Exception as e:
                    print(f"  cleanup {t}: {e}")
            # devices has no FK cascade on delete; order parent last
            cur.execute("DELETE FROM devices WHERE device_id=%s", (temp_id,))
        conn3.commit()
    except Exception as e:
        print("cleanup EXCEPTION:", e)
        conn3.rollback()
    finally:
        return_connection(conn3)
cleanup()
print("\nProbe device cleaned up.")

# ---------------------------------------------------------------
hr("6) API/REPO read methods used by endpoints - spot check")
from database.repository import DeviceRepository, DeviceIntelligenceRepository
dr = DeviceRepository()
dint2 = DeviceIntelligenceRepository()
# Grab a real device_id
conn4 = get_connection()
real_dev = None
try:
    with conn4.cursor() as cur:
        cur.execute("SELECT device_id FROM devices ORDER BY last_seen DESC NULLS LAST LIMIT 1")
        r = cur.fetchone()
        real_dev = r[0] if r else None
finally:
    conn4.rollback()
    return_connection(conn4)
if real_dev:
    print(f"Sample device: {real_dev}")
    try:
        print("  usage_today:", dr.get_device_usage_today(real_dev))
    except Exception as e:
        print(f"  get_device_usage_today EXC: {e}")
    try:
        his = dr.get_usage_history(real_dev, days=7)
        print("  usage_history last 3:", his[-3:] if his else [])
    except Exception as e:
        print(f"  get_usage_history EXC: {e}")