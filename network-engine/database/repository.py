import json

from database.connection import get_connection, return_connection
from logger import logger
from datetime import datetime, timedelta, timezone

# The single authoritative timezone for "today"/daily traffic accounting.
# The API reads today's usage with (NOW() AT TIME ZONE 'Africa/Cairo')::date, so
# the engine writer MUST use the same timezone when bucketing usage_daily. Using
# the Postgres server's default CURRENT_DATE directly would bucket by UTC and
# diverge from the API around the day boundary, showing wrong "today" totals.
APP_TZ = "Africa/Cairo"

# Ensure firewall_rules has index on device_id (created on first import)
def _ensure_firewall_rules_index():
    """Ensure firewall_rules table has index on device_id"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_firewall_rules_device_id 
                ON firewall_rules (device_id)
            """)
            # Index for the flow -> domain DNS correlation query used by the engine.
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dns_queries_response_ip
                ON dns_queries (response_ip)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dns_queries_device_domain
                ON dns_queries (device_id, domain, queried_at DESC)
            """)
        conn.commit()
        return_connection(conn)
    except Exception as e:
        logger.warning(f"Could not create firewall_rules index: {e}")

# Call on module load
_ensure_firewall_rules_index()


class DeviceRepository:
    """Repository for device operations"""

    def upsert_device(self, device_data):
        """Insert or update a device in the database"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                # Extract device data
                device_id = device_data.get("device_id")
                mac = device_data.get("mac")
                ip = device_data.get("ip")
                hostname = device_data.get("hostname")
                custom_name = device_data.get("custom_name")
                vendor = device_data.get("vendor", "Unknown")
                interface = device_data.get("interface", "")
                state = device_data.get("state", "UNKNOWN")
                
                # Try to update first
                cursor.execute(
                    """
                    UPDATE devices
                    SET ip_address = %s,
                        hostname = %s,
                        custom_name = %s,
                        vendor = %s,
                        interface_name = %s,
                        state = %s,
                        last_seen = NOW()
                    WHERE device_id = %s
                    """,
                    (ip, hostname, custom_name, vendor, interface, state, device_id)
                )
                
                # If no rows were updated, insert
                if cursor.rowcount == 0:
                    cursor.execute(
                        """
                        INSERT INTO devices (
                            device_id, mac_address, ip_address,
                            hostname, custom_name, vendor, interface_name, state,
                            first_seen, last_seen
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                        (device_id, mac, ip, hostname, custom_name, vendor, interface, state)
                    )
            
            connection.commit()
            logger.debug(f"Device {device_id} upserted")
        except Exception as e:
            connection.rollback()
            logger.error(f"Error upserting device: {e}")
            raise
        finally:
            return_connection(connection)

    def update_device_usage(self, device_id, upload_bytes=0, download_bytes=0, packets=0):
        """Increment device total usage counters"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE devices
                    SET total_upload = total_upload + %s,
                        total_download = total_download + %s,
                        total_packets = total_packets + %s,
                        last_seen = NOW()
                    WHERE device_id = %s
                    """,
                    (upload_bytes, download_bytes, packets, device_id)
                )
            connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(f"Error updating device usage: {e}")
        finally:
            return_connection(connection)

    def get_device_usage_today(self, device_id):
        """Get today's usage for a device from usage_daily"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COALESCE(download_bytes, 0),
                        COALESCE(upload_bytes, 0),
                        COALESCE(packets, 0)
                    FROM usage_daily
                    WHERE device_id = %s
                      AND day_start = (NOW() AT TIME ZONE %s)::date
                    """,
                    (device_id, APP_TZ)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "download": row[0],
                        "upload": row[1],
                        "total": row[0] + row[1],
                        "packets": row[2],
                    }
                return {"download": 0, "upload": 0, "total": 0, "packets": 0}
        finally:
            return_connection(connection)

    def get_usage_history(self, device_id, days=30):
        """Get historical usage for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        day_start::text,
                        COALESCE(download_bytes, 0),
                        COALESCE(upload_bytes, 0),
                        COALESCE(packets, 0)
                    FROM usage_daily
                    WHERE device_id = %s
                      AND day_start >= ((NOW() AT TIME ZONE %s)::date) - %s
                    ORDER BY day_start ASC
                    """,
                    (device_id, APP_TZ, days)
                )
                return [
                    {
                        "date": row[0],
                        "download": row[1],
                        "upload": row[2],
                        "total": row[1] + row[2],
                        "packets": row[3],
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)

    def get_device_limits(self, device_id):
        """Get speed limits for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, device_id, download_limit_bps, upload_limit_bps, enabled, created_at, updated_at
                    FROM speed_limits
                    WHERE device_id = %s
                    """,
                    (device_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "device_id": row[1],
                        "download_limit_bps": row[2],
                        "upload_limit_bps": row[3],
                        "enabled": row[4],
                        "created_at": row[5],
                        "updated_at": row[6],
                    }
                return None
        finally:
            return_connection(connection)

    def save_device_limits(self, device_id, download_limit_bps=None, upload_limit_bps=None, enabled=True):
        """Insert or update speed limits for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO speed_limits (device_id, download_limit_bps, upload_limit_bps, enabled, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (device_id)
                    DO UPDATE SET
                        download_limit_bps = EXCLUDED.download_limit_bps,
                        upload_limit_bps = EXCLUDED.upload_limit_bps,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                    RETURNING id
                    """,
                    (device_id, download_limit_bps, upload_limit_bps, enabled)
                )
                row = cursor.fetchone()
            connection.commit()
            return row[0] if row else None
        except Exception as e:
            connection.rollback()
            logger.error(f"Error saving device limits: {e}")
            raise
        finally:
            return_connection(connection)

    def delete_device_limits(self, device_id):
        """Delete speed limits for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM speed_limits WHERE device_id = %s",
                    (device_id,)
                )
            connection.commit()
        finally:
            return_connection(connection)

    def get_device_quota(self, device_id):
        """Get quota for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, device_id, daily_quota_bytes, weekly_quota_bytes, monthly_quota_bytes,
                           used_bytes, reset_period, reset_day, action, enabled, created_at, updated_at
                    FROM data_limits
                    WHERE device_id = %s
                    """,
                    (device_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "device_id": row[1],
                        "daily_quota_bytes": row[2],
                        "weekly_quota_bytes": row[3],
                        "monthly_quota_bytes": row[4],
                        "used_bytes": row[5],
                        "reset_period": row[6],
                        "reset_day": row[7],
                        "action": row[8],
                        "enabled": row[9],
                        "created_at": row[10],
                        "updated_at": row[11],
                    }
                return None
        finally:
            return_connection(connection)

    def save_device_quota(self, device_id, daily_quota_bytes=None, weekly_quota_bytes=None,
                          monthly_quota_bytes=None, reset_period="DAILY", reset_day=1, 
                          action="ALERT", enabled=True):
        """Insert or update quota for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO data_limits (device_id, daily_quota_bytes, weekly_quota_bytes,
                        monthly_quota_bytes, used_bytes, reset_period, reset_day, action, enabled, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 0, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (device_id)
                    DO UPDATE SET
                        daily_quota_bytes = EXCLUDED.daily_quota_bytes,
                        weekly_quota_bytes = EXCLUDED.weekly_quota_bytes,
                        monthly_quota_bytes = EXCLUDED.monthly_quota_bytes,
                        reset_period = EXCLUDED.reset_period,
                        reset_day = EXCLUDED.reset_day,
                        action = EXCLUDED.action,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                    RETURNING id
                    """,
                    (device_id, daily_quota_bytes, weekly_quota_bytes,
                     monthly_quota_bytes, reset_period, reset_day, action, enabled)
                )
                row = cursor.fetchone()
            connection.commit()
            return row[0] if row else None
        except Exception as e:
            connection.rollback()
            logger.error(f"Error saving device quota: {e}")
            raise
        finally:
            return_connection(connection)

    def delete_device_quota(self, device_id):
        """Delete quota for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM data_limits WHERE device_id = %s",
                    (device_id,)
                )
            connection.commit()
        finally:
            return_connection(connection)

    def update_quota_usage(self, device_id, used_bytes):
        """Update used bytes for a device quota"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE data_limits
                    SET used_bytes = %s, updated_at = NOW()
                    WHERE device_id = %s
                    """,
                    (used_bytes, device_id)
                )
            connection.commit()
        finally:
            return_connection(connection)

    def get_device(self, device_id):
        """Get device by device_id"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT device_id, mac_address, ip_address, hostname,
                           vendor, interface_name, state, first_seen, last_seen,
                           total_upload, total_download, total_packets
                    FROM devices
                    WHERE device_id = %s
                    """,
                    (device_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "device_id": result[0],
                        "mac": result[1],
                        "ip": result[2],
                        "hostname": result[3],
                        "vendor": result[4],
                        "interface": result[5],
                        "state": result[6],
                        "first_seen": result[7],
                        "last_seen": result[8],
                        "total_upload": result[9],
                        "total_download": result[10],
                        "total_packets": result[11],
                    }
                return None
        finally:
            return_connection(connection)

    def get_device_by_mac(self, mac):
        """Get device by MAC address"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT device_id FROM devices WHERE mac_address = %s",
                    (mac,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        finally:
            return_connection(connection)

    def get_all_devices(self):
        """Get all devices"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT device_id, mac_address, ip_address, hostname,
                           vendor, interface_name, state, first_seen, last_seen,
                           total_upload, total_download, total_packets
                    FROM devices
                    ORDER BY last_seen DESC
                    """
                )
                devices = []
                for row in cursor.fetchall():
                    devices.append({
                        "device_id": row[0],
                        "mac": row[1],
                        "ip": row[2],
                        "hostname": row[3],
                        "vendor": row[4],
                        "interface": row[5],
                        "state": row[6],
                        "first_seen": row[7],
                        "last_seen": row[8],
                        "total_upload": row[9],
                        "total_download": row[10],
                        "total_packets": row[11],
                    })
                return devices
        finally:
            return_connection(connection)

    def update_device_status(self, device_id, state):
        """Update device state"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE devices SET state = %s, last_seen = NOW() WHERE device_id = %s",
                    (state, device_id)
                )
            connection.commit()
        finally:
            return_connection(connection)

    def mark_offline(self, device_id):
        """Mark device as offline"""
        self.update_device_status(device_id, "OFFLINE")

    def mark_online(self, device_id):
        """Mark device as online"""
        self.update_device_status(device_id, "ONLINE")


class FlowRepository:
    """Repository for flow operations"""

    def save_flow(self, flow, device_id=None):
        """Save or update a flow in the database (UPSERT to prevent duplicates)"""
        # Use device_id from flow if available, otherwise use parameter
        if device_id is None and hasattr(flow, 'device_id'):
            device_id = flow.device_id
        
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                direction = flow.direction if hasattr(flow, 'direction') else 'UNKNOWN'
                cursor.execute(
                    """
                    INSERT INTO flows (
                        device_id, source_ip, destination_ip,
                        source_port, destination_port, protocol,
                        interface_name, direction, started_at, last_seen,
                        duration_seconds, packets, bytes,
                        upload_bytes, download_bytes, state
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                    ON CONFLICT (device_id, source_ip, destination_ip, source_port, destination_port, protocol, interface_name)
                    DO UPDATE SET
                        last_seen = EXCLUDED.last_seen,
                        duration_seconds = EXCLUDED.duration_seconds,
                        packets = EXCLUDED.packets,
                        bytes = EXCLUDED.bytes,
                        upload_bytes = EXCLUDED.upload_bytes,
                        download_bytes = EXCLUDED.download_bytes,
                        state = EXCLUDED.state
                    """,
                    (
                        device_id,
                        flow.source_ip,
                        flow.destination_ip,
                        flow.source_port,
                        flow.destination_port,
                        flow.protocol,
                        flow.interface,
                        direction,
                        flow.started_at,
                        flow.last_seen,
                        int(flow.duration()),
                        flow.packets,
                        flow.bytes,
                        flow.upload_bytes,
                        flow.download_bytes,
                        flow.state,
                    ),
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving flow: {e}")
            connection.rollback()
        finally:
            return_connection(connection)

    def get_active_flows(self, device_id=None, stale_seconds=300):
        """Get active flows.

        Only rows touched within the staleness window count as ACTIVE. A flow
        row whose last_seen is older than `stale_seconds` is a stale ACTIVE
        (e.g. the engine stopped without sweeping it), so it is excluded from
        the live count and marked CLOSED so retention can reclaim it.
        """
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                if device_id:
                    cursor.execute(
                        """
                        UPDATE flows
                        SET state = 'CLOSED', closed_at = COALESCE(closed_at, NOW())
                        WHERE device_id = %s AND state = 'ACTIVE'
                          AND last_seen < NOW() - make_interval(secs => %s)
                        """,
                        (device_id, stale_seconds)
                    )
                    cursor.execute(
                        """
                        SELECT * FROM flows
                        WHERE device_id = %s AND state = 'ACTIVE'
                          AND last_seen >= NOW() - make_interval(secs => %s)
                        ORDER BY last_seen DESC
                        """,
                        (device_id, stale_seconds)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE flows
                        SET state = 'CLOSED', closed_at = COALESCE(closed_at, NOW())
                        WHERE state = 'ACTIVE'
                          AND last_seen < NOW() - make_interval(secs => %s)
                        """,
                        (stale_seconds,)
                    )
                    cursor.execute(
                        """
                        SELECT * FROM flows
                        WHERE state = 'ACTIVE'
                          AND last_seen >= NOW() - make_interval(secs => %s)
                        ORDER BY last_seen DESC
                        """,
                        (stale_seconds,)
                    )
                connection.commit()
                return cursor.fetchall()
        finally:
            return_connection(connection)


class TrafficRepository:
    """Repository for traffic sample operations"""

    def save_sample(
        self,
        device_id,
        download_bytes,
        upload_bytes,
        packets,
        connections,
        download_speed_bps=0,
        upload_speed_bps=0,
    ):
        """Save a traffic sample"""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO traffic_samples (
                        device_id, download_bytes, upload_bytes,
                        packets, connections, download_speed_bps, upload_speed_bps
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        device_id,
                        download_bytes,
                        upload_bytes,
                        packets,
                        connections,
                        download_speed_bps,
                        upload_speed_bps,
                    ),
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving traffic sample: {e}")
            connection.rollback()
        finally:
            return_connection(connection)

    def save_delta_sample(
        self,
        device_id,
        download_delta,
        upload_delta,
        packets_delta,
        connections,
        download_speed_bps=0,
        upload_speed_bps=0,
        mac_address=None,
        ip_address=None,
        hostname=None,
    ):
        """Save delta-based traffic sample and update device totals + usage aggregations"""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                # GUARANTEE a devices row exists BEFORE inserting traffic_samples.
                # A device whose MAC emitted traffic but that the periodic ARP
                # scan missed would otherwise have no devices row, causing the
                # INSERT INTO traffic_samples below to fail with a FK violation
                # and roll back the ENTIRE sample (traffic lost, device invisible).
                # This upsert creates the row on first traffic and refreshes
                # last_seen/state on every subsequent sample.
                # NOTE: mac_address is NOT NULL in the schema, so we must provide
                # it. If the caller doesn't have it, we fall back to a placeholder
                # that the ARP scanner will overwrite with the real MAC.
                # Resolve a real MAC when the caller did not supply one.
                # We must NOT fabricate a random MAC (it would create a
                # misleading vendor and could collide with a real device later
                # discovered via ARP, producing duplicate rows). Resolution
                # order:
                #   1. The caller-supplied mac_address.
                #   2. The existing devices row (survives an ARP-missed packet).
                #   3. The most recent flow/connection that observed this
                #      device's source MAC (packet capture stores real frames).
                #
                # Only if every source is empty (first-ever packet and no ARP
                # entry yet) do we fall back to an explicit, deterministic
                # sentinel derived from the device_id. This sentinel starts with
                # the globally-administered-multicast bit set (locally
                # administered, multicast) so it can never collide with a real
                # unicast vendor MAC, and the ARP scanner overwrites it as soon
                # as the real MAC is learned.
                if not mac_address:
                    cursor.execute(
                        "SELECT mac_address FROM devices WHERE device_id = %s",
                        (device_id,),
                    )
                    existing = cursor.fetchone()
                    if existing and existing[0]:
                        mac_address = str(existing[0])
                    if not mac_address:
                        # First-ever traffic for this device with no ARP entry
                        # yet and no prior devices row: use a deterministic,
                        # locally-administered sentinel that cannot collide with
                        # a real unicast vendor MAC. The ARP scanner overwrites
                        # it once the real MAC is learned.
                        mac_address = f"02:00:00:00:00:{device_id[-2:]}"

                cursor.execute(
                    """
                    INSERT INTO devices (
                        device_id, mac_address, ip_address, hostname,
                        state, first_seen, last_seen
                    )
                    VALUES (%s, %s, %s, %s, 'ONLINE', NOW(), NOW())
                    ON CONFLICT (device_id)
                    DO UPDATE SET
                        state = 'ONLINE',
                        last_seen = NOW(),
                        ip_address = COALESCE(EXCLUDED.ip_address, devices.ip_address),
                        hostname = COALESCE(EXCLUDED.hostname, devices.hostname),
                        mac_address = CASE
                            WHEN devices.mac_address::text LIKE '02:00:00:00:00:%%'
                                 AND EXCLUDED.mac_address::text NOT LIKE '02:00:00:00:00:%%'
                            THEN EXCLUDED.mac_address
                            ELSE devices.mac_address
                        END
                    """,
                    (
                        device_id,
                        mac_address,
                        ip_address,
                        hostname,
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO traffic_samples (
                        device_id, download_bytes, upload_bytes,
                        packets, connections, download_speed_bps, upload_speed_bps
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        device_id,
                        download_delta,
                        upload_delta,
                        packets_delta,
                        connections,
                        download_speed_bps,
                        upload_speed_bps,
                    ),
                )

                cursor.execute(
                    """
                    UPDATE devices
                    SET total_upload = total_upload + %s,
                        total_download = total_download + %s,
                        total_packets = total_packets + %s,
                        last_seen = NOW()
                    WHERE device_id = %s
                    """,
                    (upload_delta, download_delta, packets_delta, device_id)
                )

                cursor.execute(
                    """
                    INSERT INTO usage_daily (device_id, day_start, download_bytes, upload_bytes, packets)
                    VALUES (%s, (NOW() AT TIME ZONE %s)::date, %s, %s, %s)
                    ON CONFLICT (device_id, day_start)
                    DO UPDATE SET
                        download_bytes = usage_daily.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = usage_daily.upload_bytes + EXCLUDED.upload_bytes,
                        packets = usage_daily.packets + EXCLUDED.packets
                    """,
                    (device_id, APP_TZ, download_delta, upload_delta, packets_delta)
                )

                cursor.execute(
                    """
INSERT INTO usage_hourly (device_id, hour_start, download_bytes, upload_bytes, packets)
VALUES (%s, date_trunc('hour', NOW() AT TIME ZONE %s), %s, %s, %s)
</｜DSML｜>
                    ON CONFLICT (device_id, hour_start)
                    DO UPDATE SET
                        download_bytes = usage_hourly.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = usage_hourly.upload_bytes + EXCLUDED.upload_bytes,
                        packets = usage_hourly.packets + EXCLUDED.packets
                    """,
                    (device_id, APP_TZ, download_delta, upload_delta, packets_delta)
                )

                cursor.execute(
                    """
INSERT INTO usage_monthly (device_id, month_start, download_bytes, upload_bytes, packets)
VALUES (%s, date_trunc('month', (NOW() AT TIME ZONE %s)::date)::date, %s, %s, %s)
                    ON CONFLICT (device_id, month_start)
                    DO UPDATE SET
                        download_bytes = usage_monthly.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = usage_monthly.upload_bytes + EXCLUDED.upload_bytes,
                        packets = usage_monthly.packets + EXCLUDED.packets
                    """,
                    (device_id, APP_TZ, download_delta, upload_delta, packets_delta)
                )

                # Update data_limits used_bytes based on reset_period
                cursor.execute(
                    """
                    UPDATE data_limits
                    SET used_bytes = 
                        CASE
                            WHEN reset_period = 'DAILY' THEN (
                                SELECT COALESCE(download_bytes, 0) + COALESCE(upload_bytes, 0)
                                FROM usage_daily
                                WHERE device_id = data_limits.device_id
                                  AND day_start = (NOW() AT TIME ZONE %s)::date
                            )
                            WHEN reset_period = 'WEEKLY' THEN (
                                SELECT COALESCE(SUM(download_bytes), 0) + COALESCE(SUM(upload_bytes), 0)
                                FROM usage_daily
                                WHERE device_id = data_limits.device_id
                                  AND day_start >= ((NOW() AT TIME ZONE %s)::date) - INTERVAL '6 days'
                            )
                            WHEN reset_period = 'MONTHLY' THEN (
                                SELECT COALESCE(SUM(download_bytes), 0) + COALESCE(SUM(upload_bytes), 0)
                                FROM usage_daily
                                WHERE device_id = data_limits.device_id
                                  AND day_start >= date_trunc('month', (NOW() AT TIME ZONE %s)::date)::date
                            )
                            ELSE 0
                        END,
                        updated_at = NOW()
                    WHERE data_limits.device_id = %s
                      AND data_limits.enabled = TRUE
                    """,
                    (APP_TZ, APP_TZ, APP_TZ, device_id)
                )

            connection.commit()
        except Exception as e:
            logger.error(f"Error saving delta traffic sample: {e}")
            connection.rollback()
        finally:
            return_connection(connection)

    def get_recent_samples(self, device_id, hours=1):
        """Get recent traffic samples"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT device_id, sampled_at, download_bytes,
                           upload_bytes, packets, connections
                    FROM traffic_samples
                    WHERE device_id = %s
                    AND sampled_at > NOW() - %s
                    ORDER BY sampled_at DESC
                    LIMIT 3600
                    """,
                    (device_id, timedelta(hours=hours))
                )
                return cursor.fetchall()
        finally:
            return_connection(connection)


class ConnectionRepository:
    """Repository for connection operations"""

    def save_connection(
        self,
        device_id,
        source_ip,
        destination_ip,
        source_port,
        destination_port,
        protocol,
    ):
        """Create a new connection"""
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO connections (
                        device_id, source_ip, destination_ip,
                        source_port, destination_port, protocol,
                        started_at, last_seen, state
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), 'ACTIVE')
                    """,
                    (
                        device_id,
                        source_ip,
                        destination_ip,
                        source_port,
                        destination_port,
                        protocol,
                    ),
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving connection: {e}")
            connection.rollback()
        finally:
            return_connection(connection)

    def get_active_connections(self, device_id=None, stale_seconds=300):
        """Get active connections.

        Mirrors get_active_flows: rows not touched within the staleness window
        are stale (engine stopped without closing them) and must not inflate
        the live "connections" metric. They are marked CLOSED so retention can
        reclaim them.
        """
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                if device_id:
                    cursor.execute(
                        """
                        UPDATE connections
                        SET state = 'CLOSED', closed_at = COALESCE(closed_at, NOW())
                        WHERE device_id = %s AND state = 'ACTIVE'
                          AND last_seen < NOW() - make_interval(secs => %s)
                        """,
                        (device_id, stale_seconds)
                    )
                    cursor.execute(
                        """
                        SELECT * FROM connections
                        WHERE device_id = %s AND state = 'ACTIVE'
                          AND last_seen >= NOW() - make_interval(secs => %s)
                        ORDER BY last_seen DESC
                        """,
                        (device_id, stale_seconds)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE connections
                        SET state = 'CLOSED', closed_at = COALESCE(closed_at, NOW())
                        WHERE state = 'ACTIVE'
                          AND last_seen < NOW() - make_interval(secs => %s)
                        """,
                        (stale_seconds,)
                    )
                    cursor.execute(
                        """
                        SELECT * FROM connections
                        WHERE state = 'ACTIVE'
                          AND last_seen >= NOW() - make_interval(secs => %s)
                        ORDER BY last_seen DESC
                        """,
                        (stale_seconds,)
                    )
                connection.commit()
                return cursor.fetchall()
        finally:
            return_connection(connection)


class DeviceIntelligenceRepository:
    """Repository for device intelligence data"""
    
    def save_app_usage(self, device_id, application, category, confidence, hour_start,
                       download_bytes, upload_bytes, connections, evidence=None):
        """Save attributed application usage"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO device_app_usage (
                        device_id, application, category, confidence, hour_start,
                        download_bytes, upload_bytes, connections, evidence
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, application, hour_start)
                    DO UPDATE SET
                        download_bytes = device_app_usage.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = device_app_usage.upload_bytes + EXCLUDED.upload_bytes,
                        connections = device_app_usage.connections + EXCLUDED.connections,
                        category = EXCLUDED.category,
                        confidence = EXCLUDED.confidence,
                        evidence = EXCLUDED.evidence
                    """,
                    (device_id, application, category, confidence, hour_start,
                     download_bytes, upload_bytes, connections, json.dumps(evidence) if evidence else None)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving app usage: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_domain_usage(self, device_id, domain, category, hour_start,
                          download_bytes, upload_bytes, queries, connections,
                          confidence="MEDIUM", evidence=None):
        """Save attributed domain usage"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO device_domain_usage (
                        device_id, domain, category, confidence, hour_start,
                        download_bytes, upload_bytes, queries, connections, evidence
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, domain, hour_start)
                    DO UPDATE SET
                        download_bytes = device_domain_usage.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = device_domain_usage.upload_bytes + EXCLUDED.upload_bytes,
                        queries = device_domain_usage.queries + EXCLUDED.queries,
                        connections = device_domain_usage.connections + EXCLUDED.connections,
                        category = EXCLUDED.category,
                        confidence = EXCLUDED.confidence,
                        evidence = EXCLUDED.evidence
                    """,
                    (device_id, domain, category, confidence, hour_start,
                     download_bytes, upload_bytes, queries, connections, json.dumps(evidence) if evidence else None)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving domain usage: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_category_usage(self, device_id, category, hour_start,
                            download_bytes, upload_bytes, connections):
        """Save attributed category usage"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO device_category_usage (
                        device_id, category, hour_start,
                        download_bytes, upload_bytes, connections
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, category, hour_start)
                    DO UPDATE SET
                        download_bytes = device_category_usage.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = device_category_usage.upload_bytes + EXCLUDED.upload_bytes,
                        connections = device_category_usage.connections + EXCLUDED.connections
                    """,
                    (device_id, category, hour_start,
                     download_bytes, upload_bytes, connections)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving category usage: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_protocol_usage(self, device_id, protocol, hour_start,
                            download_bytes, upload_bytes, packets, connections):
        """Save attributed protocol usage"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO device_protocol_usage (
                        device_id, protocol, hour_start,
                        download_bytes, upload_bytes, packets, connections
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, protocol, hour_start)
                    DO UPDATE SET
                        download_bytes = device_protocol_usage.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = device_protocol_usage.upload_bytes + EXCLUDED.upload_bytes,
                        packets = device_protocol_usage.packets + EXCLUDED.packets,
                        connections = device_protocol_usage.connections + EXCLUDED.connections
                    """,
                    (device_id, protocol, hour_start,
                     download_bytes, upload_bytes, packets, connections)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving protocol usage: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_peak(self, device_id, peak_type, peak_value, peak_at):
        """Save device peak usage.

        The device_peaks schema requires NOT NULL `day` (date) and `hour`
        (integer) columns, so we derive them from peak_at in SQL.
        """
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO device_peaks (device_id, peak_type, peak_value, peak_at, day, hour)
                    VALUES (%s, %s, %s, %s, %s::date, EXTRACT(HOUR FROM %s)::int)
                    """,
                    (device_id, peak_type, peak_value, peak_at, peak_at, peak_at)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving peak: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_activity_timeline(self, device_id, hour_start, is_active, total_bytes, connections):
        """Save device activity timeline"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO device_activity_timeline (device_id, hour_start, is_active, total_bytes, connections)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, hour_start)
                    DO UPDATE SET
                        is_active = EXCLUDED.is_active,
                        total_bytes = EXCLUDED.total_bytes,
                        connections = EXCLUDED.connections
                    """,
                    (device_id, hour_start, is_active, total_bytes, connections)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving activity timeline: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_sni_observation(self, device_id, sni, destination_ip, destination_port, bytes_transferred):
        """Save SNI observation"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sni_observations (device_id, sni, destination_ip, destination_port, bytes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (device_id, sni, destination_ip, destination_port, bytes_transferred)
                )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving SNI observation: {e}")
            connection.rollback()
        finally:
            return_connection(connection)
    
    def save_dns_query(self, device_id, domain, query_type, response_ip=None):
        """Save a DNS query.

        When `response_ip` is provided (from a DNS response A/AAAA answer),
        it is attached to the most recent matching query for this device/domain
        that does not yet have a response IP - or a new row is created. This
        gives the engine a device-specific domain -> IP map for evidence-based
        flow attribution.
        """
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                if response_ip:
                    # Update the most recent unanswered query for this device+domain
                    cursor.execute(
                        """
                        UPDATE dns_queries
                        SET response_ip = %s
                        WHERE id = (
                            SELECT id FROM dns_queries
                            WHERE device_id = %s
                              AND domain = %s
                              AND response_ip IS NULL
                            ORDER BY queried_at DESC
                            LIMIT 1
                        )
                        """,
                        (response_ip, device_id, domain)
                    )
                    if cursor.rowcount == 0:
                        cursor.execute(
                            """
                            INSERT INTO dns_queries (device_id, domain, query_type, response_ip)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (device_id, domain, query_type, response_ip)
                        )
                else:
                    cursor.execute(
                        """
                        INSERT INTO dns_queries (device_id, domain, query_type)
                        VALUES (%s, %s, %s)
                        """,
                        (device_id, domain, query_type)
                    )
            connection.commit()
        except Exception as e:
            logger.error(f"Error saving DNS query: {e}")
            connection.rollback()
        finally:
            return_connection(connection)

    def aggregate_dns_domains(self, hours=24, start=None, end=None):
        """Sync observed DNS queries into device_domain_usage.

        This is the evidence-based domain collection. For each hourly bucket
        within the given window (default: last 24h) we set the exact query count
        observed in dns_queries (A/AAAA only; reverse lookups are excluded).
        Flows that can later be correlated to a response_ip contribute byte
        counts through save_domain_usage().

        Idempotent by design: running it repeatedly for the same buckets simply
        re-sets `queries` to the observed value.

        Returns the number of domain records upserted.
        """
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                if start is None or end is None:
                    end = datetime.now(timezone.utc)
                    start = end - timedelta(hours=hours)
                cursor.execute(
                    """
                    INSERT INTO device_domain_usage (
                        device_id, domain, category, confidence, hour_start,
                        download_bytes, upload_bytes, queries, connections, evidence
                    )
                    SELECT
                        q.device_id,
                        q.domain,
                        NULL AS category,
                        'HIGH' AS confidence,
                        date_trunc('hour', q.queried_at AT TIME ZONE 'Africa/Cairo') AS bucket,
                        0, 0,
                        COUNT(*)::bigint AS queries,
                        0,
                        jsonb_build_object(
                            'source', 'dns',
                            'evidence_count', COUNT(*),
                            'note', 'Observed DNS queries (no response-IP correlation yet)'
                        )
                    FROM dns_queries q
                    WHERE q.domain IS NOT NULL
                      AND q.domain != ''
                      AND q.query_type IN ('A', 'AAAA', '1', '28')
                      AND q.domain NOT LIKE '%%.arpa'
                      AND q.queried_at >= %s
                      AND q.queried_at < %s
                    GROUP BY q.device_id, q.domain,
                             date_trunc('hour', q.queried_at AT TIME ZONE 'Africa/Cairo')
                    ON CONFLICT (device_id, domain, hour_start)
                    DO UPDATE SET
                        queries = EXCLUDED.queries,
                        category = COALESCE(device_domain_usage.category, EXCLUDED.category),
                        confidence = 'HIGH',
                        evidence = EXCLUDED.evidence
                    """,
                    (start, end)
                )
                connection.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error aggregating DNS domains: {e}")
            connection.rollback()
            return 0
        finally:
            return_connection(connection)
    
    def get_device_app_usage(self, device_id, hours=24):
        """Get application usage for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT application, category, confidence,
                           SUM(download_bytes) as download_bytes,
                           SUM(upload_bytes) as upload_bytes,
                           SUM(total_bytes) as total_bytes,
                           SUM(connections) as connections,
                           (array_agg(evidence ORDER BY total_bytes DESC))[1] as evidence
                    FROM device_app_usage
                    WHERE device_id = %s
                      AND hour_start > NOW() - %s
                    GROUP BY application, category, confidence
                    ORDER BY total_bytes DESC
                    """,
                    (device_id, timedelta(hours=hours))
                )
                return [
                    {
                        "name": row[0],
                        "category": row[1],
                        "confidence": row[2],
                        "download_bytes": row[3],
                        "upload_bytes": row[4],
                        "total_bytes": row[5],
                        "connections": row[6],
                        "evidence": row[7] if row[7] else None,
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_domain_usage(self, device_id, hours=24, limit=50):
        """Get domain usage for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT domain, category, confidence,
                           SUM(download_bytes) as download_bytes,
                           SUM(upload_bytes) as upload_bytes,
                           SUM(total_bytes) as total_bytes,
                           SUM(queries) as queries,
                           SUM(connections) as connections,
                           (array_agg(evidence ORDER BY total_bytes DESC))[1] as evidence
                    FROM device_domain_usage
                    WHERE device_id = %s
                      AND hour_start > NOW() - %s
                    GROUP BY domain, category, confidence
                    ORDER BY total_bytes DESC
                    LIMIT %s
                    """,
                    (device_id, timedelta(hours=hours), limit)
                )
                return [
                    {
                        "domain": row[0],
                        "category": row[1],
                        "confidence": row[2],
                        "download_bytes": row[3],
                        "upload_bytes": row[4],
                        "total_bytes": row[5],
                        "queries": row[6],
                        "connections": row[7],
                        "evidence": row[8] if row[8] else None,
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_category_usage(self, device_id, hours=24):
        """Get category usage for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT category,
                           SUM(download_bytes) as download_bytes,
                           SUM(upload_bytes) as upload_bytes,
                           SUM(total_bytes) as total_bytes,
                           SUM(connections) as connections
                    FROM device_category_usage
                    WHERE device_id = %s
                      AND hour_start > NOW() - %s
                    GROUP BY category
                    ORDER BY total_bytes DESC
                    """,
                    (device_id, timedelta(hours=hours))
                )
                return [
                    {
                        "category": row[0],
                        "download_bytes": row[1],
                        "upload_bytes": row[2],
                        "total_bytes": row[3],
                        "connections": row[4],
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_protocol_usage(self, device_id, hours=24):
        """Get protocol usage for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT protocol,
                           SUM(download_bytes) as download_bytes,
                           SUM(upload_bytes) as upload_bytes,
                           SUM(total_bytes) as total_bytes,
                           SUM(packets) as packets,
                           SUM(connections) as connections
                    FROM device_protocol_usage
                    WHERE device_id = %s
                      AND hour_start > NOW() - %s
                    GROUP BY protocol
                    ORDER BY total_bytes DESC
                    """,
                    (device_id, timedelta(hours=hours))
                )
                return [
                    {
                        "protocol": row[0],
                        "download_bytes": row[1],
                        "upload_bytes": row[2],
                        "total_bytes": row[3],
                        "packets": row[4],
                        "connections": row[5],
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_peaks(self, device_id, days=30):
        """Get device peak usage"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT peak_type, peak_value, peak_at, day, hour
                    FROM device_peaks
                    WHERE device_id = %s
                      AND peak_at > NOW() - %s
                    ORDER BY peak_at DESC
                    LIMIT 100
                    """,
                    (device_id, timedelta(days=days))
                )
                return [
                    {
                        "peak_type": row[0],
                        "peak_value": row[1],
                        "peak_at": row[2],
                        "day": row[3],
                        "hour": row[4],
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_activity_timeline(self, device_id, days=7):
        """Get device activity timeline"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT hour_start, is_active, total_bytes, connections
                    FROM device_activity_timeline
                    WHERE device_id = %s
                      AND hour_start > NOW() - %s
                    ORDER BY hour_start ASC
                    """,
                    (device_id, timedelta(days=days))
                )
                return [
                    {
                        "hour_start": row[0],
                        "is_active": row[1],
                        "total_bytes": row[2],
                        "connections": row[3],
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_sni_observations(self, device_id, hours=24):
        """Get SNI observations for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT sni, destination_ip, destination_port, observed_at, bytes
                    FROM sni_observations
                    WHERE device_id = %s
                      AND observed_at > NOW() - %s
                    ORDER BY observed_at DESC
                    LIMIT 100
                    """,
                    (device_id, timedelta(hours=hours))
                )
                return [
                    {
                        "sni": row[0],
                        "destination_ip": row[1],
                        "destination_port": row[2],
                        "observed_at": row[3],
                        "bytes": row[4],
                    }
                    for row in cursor.fetchall()
                ]
        finally:
            return_connection(connection)
    
    def get_device_intelligence_summary(self, device_id, hours=24):
        """Get comprehensive device intelligence summary"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                # Get total traffic in period
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(SUM(download_bytes), 0) as total_download,
                        COALESCE(SUM(upload_bytes), 0) as total_upload,
                        COALESCE(SUM(total_bytes), 0) as total_bytes,
                        COALESCE(SUM(connections), 0) as total_connections
                    FROM device_app_usage
                    WHERE device_id = %s
                      AND hour_start > NOW() - %s
                    """,
                    (device_id, timedelta(hours=hours))
                )
                total_row = cursor.fetchone()
                
                total_download = total_row[0] if total_row else 0
                total_upload = total_row[1] if total_row else 0
                total_bytes = total_row[2] if total_row else 0
                total_connections = total_row[3] if total_row else 0
            
            return {
                "device_id": device_id,
                "period_hours": hours,
                "total_download_bytes": total_download,
                "total_upload_bytes": total_upload,
                "total_bytes": total_bytes,
                "total_connections": total_connections,
                "top_applications": self.get_device_app_usage(device_id, hours)[:10],
                "top_domains": self.get_device_domain_usage(device_id, hours)[:10],
                "categories": self.get_device_category_usage(device_id, hours),
                "protocols": self.get_device_protocol_usage(device_id, hours),
                "peaks": self.get_device_peaks(device_id, days=hours//24 + 1)[:20],
                "activity_timeline": self.get_device_activity_timeline(device_id, days=hours//24 + 1),
            }
        finally:
            return_connection(connection)
