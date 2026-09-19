from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from database.connection import get_connection, return_connection
from api.security import get_current_user, require_permission
from database.audit import log_admin_action
from api.websocket import manager as ws_manager

router = APIRouter()


@router.get("/status")
def system_status():
    """
    Return real-time system component status with real metrics from PostgreSQL.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Check database connectivity
            cursor.execute("SELECT 1")
            db_ok = cursor.fetchone() is not None

            if db_ok:
                # Real device counts
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total_devices,
                        COUNT(*) FILTER (WHERE state = 'ONLINE') AS online_devices,
                        COUNT(*) FILTER (WHERE state = 'OFFLINE') AS offline_devices
                    FROM devices
                    """
                )
                row = cursor.fetchone()
                total_devices = row[0] or 0
                online_devices = row[1] or 0
                offline_devices = row[2] or 0

                # Real active connections from connections table
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM connections
                    WHERE state = 'ACTIVE'
                    """
                )
                active_connections = cursor.fetchone()[0] or 0

                # Real active flows
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM flows
                    WHERE state = 'ACTIVE'
                    """
                )
                active_flows = cursor.fetchone()[0] or 0

                # Real total traffic from devices table
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(total_download), 0),
                        COALESCE(SUM(total_upload), 0)
                    FROM devices
                    """
                )
                row = cursor.fetchone()
                total_download = row[0] or 0
                total_upload = row[1] or 0

                # Real today's usage (Egypt timezone)
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(download_bytes), 0),
                        COALESCE(SUM(upload_bytes), 0)
                    FROM usage_daily
                    WHERE day_start = (NOW() AT TIME ZONE 'Africa/Cairo')::date
                    """
                )
                row = cursor.fetchone()
                today_download = row[0] or 0
                today_upload = row[1] or 0

                # Latest real-time speed from traffic_samples (most recent sample per device, summed)
                cursor.execute(
                    """
                    WITH latest_samples AS (
                        SELECT DISTINCT ON (device_id) 
                            device_id,
                            download_speed_bps,
                            upload_speed_bps,
                            sampled_at
                        FROM traffic_samples
                        WHERE sampled_at > NOW() - INTERVAL '2 minutes'
                        ORDER BY device_id, sampled_at DESC
                    )
                    SELECT 
                        COALESCE(SUM(download_speed_bps), 0),
                        COALESCE(SUM(upload_speed_bps), 0)
                    FROM latest_samples
                    """
                )
                row = cursor.fetchone()
                current_download_speed = row[0] or 0
                current_upload_speed = row[1] or 0

                # Peak bandwidth from traffic_samples (true peak over 24h)
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(download_speed_bps + upload_speed_bps), 0)
                    FROM traffic_samples
                    WHERE sampled_at > NOW() - INTERVAL '24 hours'
                    """
                )
                peak_bandwidth_bps = cursor.fetchone()[0] or 0
    except Exception:
        db_ok = False
        total_devices = 0
        online_devices = 0
        offline_devices = 0
        active_connections = 0
        active_flows = 0
        total_download = 0
        total_upload = 0
        today_download = 0
        today_upload = 0
        current_download_speed = 0
        current_upload_speed = 0
        peak_bandwidth_bps = 0
    finally:
        return_connection(connection)

    return {
        "engine": "running",
        "database": "connected" if db_ok else "disconnected",
        "capture": "running",
        "api": "running",
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "active_connections": active_connections,
        "active_flows": active_flows,
        "total_download": total_download,
        "total_upload": total_upload,
        "today_download": today_download,
        "today_upload": today_upload,
        "current_download_speed_bps": current_download_speed,
        "current_upload_speed_bps": current_upload_speed,
        "current_speed_bps": current_download_speed + current_upload_speed,
        "peak_bandwidth_bps": peak_bandwidth_bps,
    }


@router.get("/interfaces")
def get_interfaces(user=Depends(get_current_user)):
    """
    Return all network interfaces from the database.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    name,
                    description,
                    mac_address::text,
                    ip_address::text,
                    network::text,
                    speed_mbps,
                    status,
                    created_at
                FROM interfaces
                ORDER BY name
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "name": row[0],
                "description": row[1],
                "mac": row[2],
                "ip": row[3],
                "network": row[4],
                "speed_mbps": row[5],
                "status": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load interfaces: {error}",
        )
    finally:
        return_connection(connection)


class SettingsUpdate(BaseModel):
    system_name: Optional[str] = None
    admin_email: Optional[str] = None
    dns_server: Optional[str] = None
    bandwidth_limit: Optional[int] = None


@router.get("/settings")
def get_settings(user=Depends(require_permission("settings:read"))):
    """
    Return all system settings from the database.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT key, value, updated_at
                FROM settings
                ORDER BY key
                """
            )
            rows = cursor.fetchall()

        settings = {}
        for row in rows:
            settings[row[0]] = row[1]

        return {
            "system_name": settings.get("system_name", "NetworkMonitor"),
            "admin_email": settings.get("admin_email", ""),
            "dns_server": settings.get("dns_server", ""),
            "bandwidth_limit": int(settings.get("bandwidth_limit", 0) or 0),
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load settings: {error}",
        )
    finally:
        return_connection(connection)


class BroadcastRequest(BaseModel):
    type: str
    data: Dict[str, Any]


@router.post("/broadcast")
def broadcast_message(request: BroadcastRequest):
    """
    Broadcast a message to all WebSocket clients.
    This endpoint is used by the engine process to send real-time updates.
    No authentication required - called from internal engine process.
    """
    try:
        message = {"type": request.type, "data": request.data}
        ws_manager.broadcast_threadsafe(message)
        return {"status": "ok", "message": "Broadcast sent"}
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to broadcast: {error}",
        )


@router.put("/settings")
def update_settings(data: SettingsUpdate, user=Depends(require_permission("settings:write"))):
    """
    Update system settings.
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT key, value FROM settings WHERE key IN ('system_name', 'admin_email', 'dns_server', 'bandwidth_limit')")
            old_settings = {row[0]: row[1] for row in cursor.fetchall()}
            
            updates = {
                "system_name": data.system_name,
                "admin_email": data.admin_email,
                "dns_server": data.dns_server,
                "bandwidth_limit": str(data.bandwidth_limit) if data.bandwidth_limit is not None else None,
            }

            for key, value in updates.items():
                if value is not None:
                    cursor.execute(
                        """
                        INSERT INTO settings (key, value, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (key)
                        DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                        """,
                        (key, value),
                    )

        connection.commit()
        
        # Audit log
        new_settings = {
            "system_name": data.system_name or old_settings.get("system_name", "NetworkMonitor"),
            "admin_email": data.admin_email or old_settings.get("admin_email", ""),
            "dns_server": data.dns_server or old_settings.get("dns_server", ""),
            "bandwidth_limit": data.bandwidth_limit or int(old_settings.get("bandwidth_limit", 0) or 0),
        }
        log_admin_action(user["username"], "SETTINGS", "system", str(old_settings), str(new_settings))
        
        return {
            "system_name": data.system_name or "NetworkMonitor",
            "admin_email": data.admin_email or "",
            "dns_server": data.dns_server or "",
            "bandwidth_limit": data.bandwidth_limit or 0,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {error}",
        )
    finally:
        return_connection(connection)
