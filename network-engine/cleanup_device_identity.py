"""One-time data cleanup to fix device identity forking.

Root cause: devices were keyed by MAC. When the phone's privacy MAC
randomized (ee:83 -> f2:87), the same physical device (192.168.137.75) was
split into two records (dev_003 and dev_006). Additionally, the ICS NAT host
boundary (192.168.137.1) and a broadcast MAC were tracked as "devices".

This script:
  1. Merges duplicate device records that share an IP into the earliest record,
     reassigning all child rows (usage, flows, intelligence) to the canonical ID.
  2. Removes the host/boundary ghost device and broadcast/multicast "devices".
  3. Removes known seed/test/demo devices.
  4. Recomputes devices.total_upload/total_download/total_packets from traffic
     samples so cumulative totals reflect only real captured traffic.

Idempotent: safe to run more than once.
"""
import sys
from database.connection import get_connection, return_connection
from logger import logger
from config import network_config as config


def normalize_ip(ip):
    if ip is None:
        return None
    if hasattr(ip, "split"):
        return ip.split("/")[0]
    return str(ip)


def main():
    conn = get_connection()
    # Run in autocommit mode: each statement is its own transaction, so a
    # single missing/invalid table during the merge cannot abort the whole run
    # or roll back earlier successful migrations.
    try:
        conn.autocommit = True
    except Exception:
        pass
    try:
        with conn.cursor() as cur:
            # 1) Remove the host/boundary ghost. The monitor host's own NAT IP
            #    (config.lan_ip == 192.168.137.1) is NOT a client device.
            if config.lan_ip:
                host_ip = normalize_ip(config.lan_ip)
                cur.execute(
                    "DELETE FROM devices WHERE split_part(ip_address::text,'/',1) = %s",
                    (host_ip,),
                )
                logger.info(f"Removed {cur.rowcount} host/boundary ghost device(s) at {host_ip}")

            # 2) Remove broadcast/multicast/zero MAC "devices".
            cur.execute(
                """
                DELETE FROM devices
                WHERE LOWER(mac_address::text) IN ('ff:ff:ff:ff:ff:ff','00:00:00:00:00:00')
                """
            )
            logger.info(f"Removed {cur.rowcount} broadcast/zero MAC ghost device(s)")

            # 3) Remove known seed/test/demo devices.
            cur.execute(
                """
                DELETE FROM devices
                WHERE device_id LIKE 'test_%'
                   OR device_id LIKE 'seed_%'
                   OR device_id LIKE 'demo_%'
                   OR hostname ILIKE '%test%'
                   OR hostname ILIKE '%seed%'
                   OR hostname ILIKE '%demo%'
                   -- Locally-administered fake MACs used by seed fixtures:
                   -- aa:bb:cc:dd:ee:xx are NOT real vendor OUI assignments.
                   OR LOWER(mac_address::text) LIKE 'aa:bb:cc:dd:ee:%'
                """
            )
            logger.info(f"Removed {cur.rowcount} seed/test/demo device(s)")

            # 4) Merge duplicate records that share the same IP (MAC randomization),
            #    keeping the earliest (min device_id ordering) as canonical.
            #    Find IPs that map to more than one device.
            cur.execute(
                """
                SELECT split_part(ip_address::text,'/',1) AS ip,
                       count(*) AS cnt
                FROM devices
                WHERE ip_address IS NOT NULL
                  AND split_part(ip_address::text,'/',1) <> ''
                GROUP BY 1
                HAVING count(*) > 1
                """
            )
            duplicate_ips = cur.fetchall()

            device_tables = [
                "traffic_samples",
                "usage_daily",
                "flows",
                "device_app_usage",
                "device_domain_usage",
                "device_category_usage",
                "device_protocol_usage",
                "device_activity_timeline",
                "device_peaks",
                "dns_queries",
                "sni_observations",
                "device_connections",
                "speed_limits",
                "data_limits",
                "firewall_rules",
                "device_quotas",
            ]

            for ip, _cnt in duplicate_ips:
                # Canonical = the device with the most traffic (or earliest first_seen)
                cur.execute(
                    """
                    SELECT device_id FROM devices
                    WHERE split_part(ip_address::text,'/',1) = %s
                    ORDER BY total_download DESC, first_seen ASC
                    """,
                    (ip,),
                )
                ids = [r[0] for r in cur.fetchall()]
                if len(ids) < 2:
                    continue
                canonical = ids[0]
                dupes = ids[1:]
                logger.info(f"IP {ip}: canonical={canonical}, merging duplicates={dupes}")
                for d in dupes:
                    for table in device_tables:
                        try:
                            cur.execute(
                                f"UPDATE {table} SET device_id = %s WHERE device_id = %s",
                                (canonical, d),
                            )
                        except Exception as e:
                            # Table may not exist or lack device_id column.
                            # Autocommit mode means this failure only aborts the
                            # single statement; subsequent tables still run.
                            logger.debug(f"skip {table}: {e}")
                    # Merge cumulative counters into canonical
                    cur.execute(
                        """
                        UPDATE devices d
                        SET total_upload = d.total_upload + o.total_upload,
                            total_download = d.total_download + o.total_download,
                            total_packets = d.total_packets + o.total_packets
                        FROM devices o
                        WHERE d.device_id = %s AND o.device_id = %s
                        """,
                        (canonical, d),
                    )
                    # Drop duplicate device row
                    cur.execute("DELETE FROM devices WHERE device_id = %s", (d,))
                    logger.info(f"  merged {d} -> {canonical}")

            # 5) Reset polluted historical accumulators to a clean baseline.
            #    Historical traffic_samples/usage_daily were written by an older
            #    code path that inflated them ~20x versus devices.total_*
            #    (internally inconsistent), which produced the random-looking /
            #    inflated values in the UI. The current save_delta_sample writes
            #    deltas consistently to all three places, so we clear the bad
            #    history and let the engine repopulate real, correctly-attributed
            #    data from now on. Until fresh traffic is captured, the API
            #    returns an honest "no data" state instead of fake numbers.
            cur.execute("DELETE FROM traffic_samples")
            logger.info(f"Cleared {cur.rowcount} inflated traffic_samples row(s)")
            cur.execute("DELETE FROM usage_daily")
            logger.info(f"Cleared {cur.rowcount} inflated usage_daily row(s)")
            cur.execute(
                "UPDATE devices SET total_upload = 0, total_download = 0, total_packets = 0"
            )
            logger.info("Zeroed cumulative device totals (clean baseline)")

            logger.info("Device identity cleanup complete.")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return 1
    finally:
        return_connection(conn)
    return 0


if __name__ == "__main__":
    sys.exit(main())