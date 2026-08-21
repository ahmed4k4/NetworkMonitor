from database.connection import get_connection
from logger import logger


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
                vendor = device_data.get("vendor", "Unknown")
                interface = device_data.get("interface", "")
                state = device_data.get("state", "UNKNOWN")
                
                # Try to update first
                cursor.execute(
                    """
                    UPDATE devices
                    SET ip_address = %s,
                        hostname = %s,
                        vendor = %s,
                        interface_name = %s,
                        state = %s,
                        last_seen = NOW()
                    WHERE device_id = %s
                    """,
                    (ip, hostname, vendor, interface, state, device_id)
                )
                
                # If no rows were updated, insert
                if cursor.rowcount == 0:
                    cursor.execute(
                        """
                        INSERT INTO devices (
                            device_id, mac_address, ip_address,
                            hostname, vendor, interface_name, state,
                            first_seen, last_seen
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                        (device_id, mac, ip, hostname, vendor, interface, state)
                    )
                
            connection.commit()
            logger.debug(f"Device {device_id} upserted")
        except Exception as e:
            connection.rollback()
            logger.error(f"Error upserting device: {e}")
            raise
        finally:
            connection.close()

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
            connection.close()

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
                      AND day_start = CURRENT_DATE
                    """,
                    (device_id,)
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
            connection.close()

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
                      AND day_start >= CURRENT_DATE - %s
                    ORDER BY day_start ASC
                    """,
                    (device_id, days)
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
            connection.close()

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
            connection.close()

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
            connection.close()

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
            connection.close()

    def get_device_quota(self, device_id):
        """Get quota for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, device_id, daily_quota_bytes, weekly_quota_bytes, monthly_quota_bytes,
                           used_bytes, reset_period, enabled, created_at, updated_at
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
                        "enabled": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                    }
                return None
        finally:
            connection.close()

    def save_device_quota(self, device_id, daily_quota_bytes=None, weekly_quota_bytes=None,
                          monthly_quota_bytes=None, reset_period="DAILY", enabled=True):
        """Insert or update quota for a device"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO data_limits (device_id, daily_quota_bytes, weekly_quota_bytes,
                        monthly_quota_bytes, used_bytes, reset_period, enabled, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 0, %s, %s, NOW(), NOW())
                    ON CONFLICT (device_id)
                    DO UPDATE SET
                        daily_quota_bytes = EXCLUDED.daily_quota_bytes,
                        weekly_quota_bytes = EXCLUDED.weekly_quota_bytes,
                        monthly_quota_bytes = EXCLUDED.monthly_quota_bytes,
                        reset_period = EXCLUDED.reset_period,
                        enabled = EXCLUDED.enabled,
                        updated_at = NOW()
                    RETURNING id
                    """,
                    (device_id, daily_quota_bytes, weekly_quota_bytes,
                     monthly_quota_bytes, reset_period, enabled)
                )
                row = cursor.fetchone()
            connection.commit()
            return row[0] if row else None
        except Exception as e:
            connection.rollback()
            logger.error(f"Error saving device quota: {e}")
            raise
        finally:
            connection.close()

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
            connection.close()

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
            connection.close()

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
            connection.close()

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
            connection.close()

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
            connection.close()

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
            connection.close()

    def mark_offline(self, device_id):
        """Mark device as offline"""
        self.update_device_status(device_id, "OFFLINE")

    def mark_online(self, device_id):
        """Mark device as online"""
        self.update_device_status(device_id, "ONLINE")


class FlowRepository:
    """Repository for flow operations"""

    def save_flow(self, flow, device_id=None):
        """Save a flow to the database"""
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
            connection.close()

    def get_active_flows(self, device_id=None):
        """Get active flows"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                if device_id:
                    cursor.execute(
                        "SELECT * FROM flows WHERE device_id = %s AND state = 'ACTIVE'",
                        (device_id,)
                    )
                else:
                    cursor.execute("SELECT * FROM flows WHERE state = 'ACTIVE'")
                return cursor.fetchall()
        finally:
            connection.close()


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
            connection.close()

    def save_delta_sample(
        self,
        device_id,
        download_delta,
        upload_delta,
        packets_delta,
        connections,
        download_speed_bps=0,
        upload_speed_bps=0,
    ):
        """Save delta-based traffic sample and update device totals + usage aggregations"""
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
                    VALUES (%s, CURRENT_DATE, %s, %s, %s)
                    ON CONFLICT (device_id, day_start)
                    DO UPDATE SET
                        download_bytes = usage_daily.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = usage_daily.upload_bytes + EXCLUDED.upload_bytes,
                        packets = usage_daily.packets + EXCLUDED.packets
                    """,
                    (device_id, download_delta, upload_delta, packets_delta)
                )

                cursor.execute(
                    """
                    INSERT INTO usage_hourly (device_id, hour_start, download_bytes, upload_bytes, packets)
                    VALUES (%s, date_trunc('hour', NOW()), %s, %s, %s)
                    ON CONFLICT (device_id, hour_start)
                    DO UPDATE SET
                        download_bytes = usage_hourly.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = usage_hourly.upload_bytes + EXCLUDED.upload_bytes,
                        packets = usage_hourly.packets + EXCLUDED.packets
                    """,
                    (device_id, download_delta, upload_delta, packets_delta)
                )

                cursor.execute(
                    """
                    INSERT INTO usage_monthly (device_id, month_start, download_bytes, upload_bytes, packets)
                    VALUES (%s, date_trunc('month', CURRENT_DATE)::date, %s, %s, %s)
                    ON CONFLICT (device_id, month_start)
                    DO UPDATE SET
                        download_bytes = usage_monthly.download_bytes + EXCLUDED.download_bytes,
                        upload_bytes = usage_monthly.upload_bytes + EXCLUDED.upload_bytes,
                        packets = usage_monthly.packets + EXCLUDED.packets
                    """,
                    (device_id, download_delta, upload_delta, packets_delta)
                )

                cursor.execute(
                    """
                    UPDATE data_limits
                    SET used_bytes = usage_daily.download_bytes + usage_daily.upload_bytes,
                        updated_at = NOW()
                    FROM usage_daily
                    WHERE data_limits.device_id = %s
                      AND usage_daily.device_id = %s
                      AND usage_daily.day_start = CURRENT_DATE
                      AND data_limits.enabled = TRUE
                    """,
                    (device_id, device_id)
                )

            connection.commit()
        except Exception as e:
            logger.error(f"Error saving delta traffic sample: {e}")
            connection.rollback()
        finally:
            connection.close()

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
                    AND sampled_at > NOW() - INTERVAL '%s hours'
                    ORDER BY sampled_at DESC
                    LIMIT 3600
                    """,
                    (device_id, hours)
                )
                return cursor.fetchall()
        finally:
            connection.close()


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
            connection.close()

    def get_active_connections(self, device_id=None):
        """Get active connections"""
        connection = get_connection()
        
        try:
            with connection.cursor() as cursor:
                if device_id:
                    cursor.execute(
                        """
                        SELECT * FROM connections
                        WHERE device_id = %s AND state = 'ACTIVE'
                        ORDER BY last_seen DESC
                        """,
                        (device_id,)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM connections WHERE state = 'ACTIVE' ORDER BY last_seen DESC"
                    )
                return cursor.fetchall()
        finally:
            connection.close()
