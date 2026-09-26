from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from control.engine import ControlEngine

from api.security import (
    get_current_user,
    require_roles,
    require_permission,
)

from database.connection import (
    get_connection,
    return_connection,
)

from database.repository import DeviceRepository
from database.audit import log_admin_action
from config import network_config as config

router = APIRouter()

control_engine = ControlEngine()

from typing import Optional
from pydantic import BaseModel


class DeviceLimitRequest(BaseModel):
    download_kbps: Optional[int] = None
    upload_kbps: Optional[int] = None
    download_limit: Optional[int] = None
    upload_limit: Optional[int] = None
    enabled: Optional[bool] = True


class BlockRequest(BaseModel):
    reason: Optional[str] = None
    enabled: Optional[bool] = True


class DeviceQuotaRequest(BaseModel):
    daily_quota_mb: Optional[float] = None
    weekly_quota_mb: Optional[float] = None
    monthly_quota_mb: Optional[float] = None
    quota_bytes: Optional[int] = None
    reset_period: Optional[str] = "DAILY"  # DAILY, WEEKLY, MONTHLY
    reset_day: Optional[int] = 1
    enabled: Optional[bool] = True
    action: Optional[str] = "ALERT"  # BLOCK, THROTTLE, ALERT


class DeviceNameRequest(BaseModel):
    name: str
# ============================================================
# GET ALL DEVICES
# ============================================================

@router.get("/")
def get_devices(
    user=Depends(get_current_user),
):
    """
    Return all discovered network devices with real usage data.
    """

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    d.device_id,
                    d.mac_address::text,
                    split_part(d.ip_address::text, '/', 1) AS ip_address,
                    d.hostname,
                    d.custom_name,
                    d.vendor,
                    d.interface_name,
                    d.state,
                    d.first_seen,
                    d.last_seen,
                    d.total_upload,
                    d.total_download,
                    COALESCE(ud.download_bytes, 0) AS download_today,
                    COALESCE(ud.upload_bytes, 0) AS upload_today,
                    COALESCE(ts.download_speed_bps, 0) AS download_speed_bps,
                    COALESCE(ts.upload_speed_bps, 0) AS upload_speed_bps,
                    sl.id AS limit_id,
                    sl.download_limit_bps,
                    sl.upload_limit_bps,
                    sl.enabled AS limit_enabled,
                    dl.id AS quota_id,
                    dl.daily_quota_bytes,
                    dl.weekly_quota_bytes,
                    dl.monthly_quota_bytes,
                    dl.reset_period,
                    dl.used_bytes,
                    dl.enabled AS quota_enabled
                FROM devices d
                LEFT JOIN usage_daily ud
                    ON ud.device_id = d.device_id
                    AND ud.day_start = (NOW() AT TIME ZONE %s)::date
                LEFT JOIN LATERAL (
                    SELECT download_speed_bps, upload_speed_bps
                    FROM traffic_samples
                    WHERE device_id = d.device_id
                    ORDER BY sampled_at DESC
                    LIMIT 1
                ) ts ON TRUE
                LEFT JOIN speed_limits sl
                    ON sl.device_id = d.device_id
                LEFT JOIN data_limits dl
                    ON dl.device_id = d.device_id
                ORDER BY
                    CASE
                        WHEN d.state = 'ONLINE'
                        THEN 0
                        ELSE 1
                    END,
                    d.last_seen DESC
                """,
                (config.tz,)
            )

            rows = cursor.fetchall()

        devices = []

        for row in rows:
            download_today = row[12] or 0
            upload_today = row[13] or 0
            download_speed = row[14] or 0
            upload_speed = row[15] or 0
            # Columns: 16=limit_id, 17=dl_limit, 18=ul_limit, 19=limit_enabled,
            # 20=quota_id, 21=daily_quota, 22=weekly_quota, 23=monthly_quota,
            # 24=reset_period, 25=used_bytes, 26=quota_enabled
            reset_period = row[24] or "DAILY"
            if reset_period == "DAILY":
                quota_bytes = row[21]
            elif reset_period == "WEEKLY":
                quota_bytes = row[22]
            elif reset_period == "MONTHLY":
                quota_bytes = row[23]
            else:
                quota_bytes = row[21] or row[22] or row[23]
            used_bytes = row[25] or 0
            usage_pct = (
                (used_bytes / quota_bytes * 100)
                if quota_bytes and quota_bytes > 0
                else 0
            )

            devices.append(
                {
                    "device_id": row[0],
                    "mac": row[1],
                    "ip": row[2],
                    "hostname": row[3],
                    "custom_name": row[4],
                    "vendor": row[5],
                    "interface": row[6],
                    "state": row[7],
                    "first_seen": row[8],
                    "last_seen": row[9],
                    "upload": row[10] or 0,
                    "download": row[11] or 0,
                    "download_today": download_today,
                    "upload_today": upload_today,
                    "total_today": download_today + upload_today,
                    "download_speed_bps": download_speed,
                    "upload_speed_bps": upload_speed,
                    "current_speed_bps": download_speed + upload_speed,
                    "usage_percentage": round(usage_pct, 1),
                    "quota_bytes": quota_bytes,
                    "quota_used_bytes": used_bytes,
                    "quota_remaining_bytes": max(0, (quota_bytes or 0) - used_bytes),
                    "quota_enabled": row[25],
                    "limit_id": row[16],
                    "download_limit_bps": row[17],
                    "upload_limit_bps": row[18],
                    "limit_enabled": bool(row[19]) if row[19] is not None else False,
                }
            )

        return devices

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load devices: {error}",
        )

    finally:

        return_connection(connection)


# ============================================================
# GET DEVICE BY ID
# ============================================================

@router.get("/{device_id}")
def get_device(
    device_id: str,
    user=Depends(get_current_user),
):
    """
    Return detailed information about one device with real usage data.
    """

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    d.device_id,
                    d.mac_address::text,
                    split_part(d.ip_address::text, '/', 1) AS ip_address,
                    d.hostname,
                    d.custom_name,
                    d.vendor,
                    d.interface_name,
                    d.state,
                    d.first_seen,
                    d.last_seen,
                    d.total_upload,
                    d.total_download,
                    COALESCE(ud.download_bytes, 0) AS download_today,
                    COALESCE(ud.upload_bytes, 0) AS upload_today,
                    COALESCE(ts.download_speed_bps, 0) AS download_speed_bps,
                    COALESCE(ts.upload_speed_bps, 0) AS upload_speed_bps,
                    sl.id AS limit_id,
                    sl.download_limit_bps,
                    sl.upload_limit_bps,
                    sl.enabled AS limit_enabled,
                    dl.id AS quota_id,
                    dl.daily_quota_bytes,
                    dl.weekly_quota_bytes,
                    dl.monthly_quota_bytes,
                    dl.reset_period,
                    dl.used_bytes,
                    dl.enabled AS quota_enabled
                FROM devices d
                LEFT JOIN usage_daily ud
                    ON ud.device_id = d.device_id
                    AND ud.day_start = (NOW() AT TIME ZONE %s)::date
                LEFT JOIN LATERAL (
                    SELECT download_speed_bps, upload_speed_bps
                    FROM traffic_samples
                    WHERE device_id = d.device_id
                    ORDER BY sampled_at DESC
                    LIMIT 1
                ) ts ON TRUE
                LEFT JOIN speed_limits sl
                    ON sl.device_id = d.device_id
                LEFT JOIN data_limits dl
                    ON dl.device_id = d.device_id
                WHERE d.device_id = %s
                """,
                (config.tz, device_id),
            )

            row = cursor.fetchone()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Device not found",
            )

        download_today = row[12] or 0
        upload_today = row[13] or 0
        download_speed = row[14] or 0
        upload_speed = row[15] or 0
        # Columns: 16=limit_id, 17=dl_limit, 18=ul_limit, 19=limit_enabled,
        # 20=quota_id, 21=daily_quota, 22=weekly_quota, 23=monthly_quota,
        # 24=reset_period, 25=used_bytes, 26=quota_enabled
        reset_period = row[24] or "DAILY"
        if reset_period == "DAILY":
            quota_bytes = row[21]
        elif reset_period == "WEEKLY":
            quota_bytes = row[22]
        elif reset_period == "MONTHLY":
            quota_bytes = row[23]
        else:
            quota_bytes = row[21] or row[22] or row[23]
        used_bytes = row[25] or 0
        usage_pct = (
            (used_bytes / quota_bytes * 100)
            if quota_bytes and quota_bytes > 0
            else 0
        )

        # Get usage history
        repo = DeviceRepository()
        history = repo.get_usage_history(device_id, days=30)

        return {
            "device_id": row[0],
            "mac": row[1],
            "ip": row[2],
            "hostname": row[3],
            "custom_name": row[4],
            "vendor": row[5],
            "interface": row[6],
            "state": row[7],
            "first_seen": row[8],
            "last_seen": row[9],
            "upload": row[10] or 0,
            "download": row[11] or 0,
            "download_today": download_today,
            "upload_today": upload_today,
            "total_today": download_today + upload_today,
            "download_speed_bps": download_speed,
            "upload_speed_bps": upload_speed,
            "current_speed_bps": download_speed + upload_speed,
            "usage_percentage": round(usage_pct, 1),
            "quota_bytes": quota_bytes,
            "quota_used_bytes": used_bytes,
            "quota_remaining_bytes": max(0, (quota_bytes or 0) - used_bytes),
            "quota_enabled": row[25],
            "limit_id": row[16],
            "download_limit_bps": row[17],
            "upload_limit_bps": row[18],
            "limit_enabled": bool(row[19]) if row[19] is not None else False,
            "history": history,
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load device: {error}",
        )

    finally:

        return_connection(connection)


# ============================================================
# GET DEVICE BY MAC ADDRESS
# ============================================================

@router.get("/mac/{mac_address}")
def get_device_by_mac(
    mac_address: str,
    user=Depends(get_current_user),
):
    """
    Return a device using its MAC address.
    """

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    device_id,
                    mac_address::text,
                    split_part(ip_address::text, '/', 1) AS ip_address,
                    hostname,
                    custom_name,
                    vendor,
                    interface_name,
                    state,
                    first_seen,
                    last_seen,
                    total_upload,
                    total_download
                FROM devices
                WHERE LOWER(mac_address::text) = LOWER(%s)
                """,
                (mac_address,),
            )

            row = cursor.fetchone()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Device not found",
            )

        return {
            "device_id": row[0],
            "mac": row[1],
            "ip": row[2],
            "hostname": row[3],
            "custom_name": row[4],
            "vendor": row[5],
            "interface": row[6],
            "state": row[7],
            "first_seen": row[8],
            "last_seen": row[9],
            "upload": row[10] or 0,
            "download": row[11] or 0,
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to find device: {error}",
        )

    finally:

        return_connection(connection)

@router.post("/{device_id}/block")
def block_device(
    device_id: str,
    ip: Optional[str] = None,
    user=Depends(require_permission("control:firewall:write")),
):

    if not ip:
        repo = DeviceRepository()
        device = repo.get_device(device_id)
        if device and device.get("ip"):
            ip = device["ip"]

    if not ip:
        raise HTTPException(status_code=400, detail="Device has no IP address to block.")

    result = control_engine.block(
        device_id,
        ip,
    )
    
    # Audit log
    log_admin_action(user["username"], "BLOCK", device_id, "unblocked", f"blocked at IP {ip}")
    
    return result

@router.post("/{device_id}/unblock")
def unblock_device(
    device_id: str,
    user=Depends(require_permission("control:firewall:write")),
):

    result = control_engine.unblock(device_id)
    
    # Audit log
    log_admin_action(user["username"], "UNBLOCK", device_id, "blocked", "unblocked")
    
    return result

@router.post("/{device_id}/limit")
def limit_device(
    device_id: str,
    data: DeviceLimitRequest,
    ip: Optional[str] = None,
    user=Depends(require_permission("control:limits:write")),
):
    """Set or update speed limits for a device and persist to database."""
    try:
        if not ip:
            repo = DeviceRepository()
            device = repo.get_device(device_id)
            if device and device.get("ip"):
                ip = device["ip"]

        # Convert KB/s (data.download_limit) to bits per second
        download_bps = None
        upload_bps = None
        if data.download_limit is not None:
            download_bps = int(data.download_limit * 1024 * 8)
        if data.upload_limit is not None:

            upload_bps = int(data.upload_limit * 1024 * 8)

        # Persist limits to database
        repo = DeviceRepository()
        limit_id = repo.save_device_limits(
            device_id=device_id,
            download_limit_bps=download_bps,
            upload_limit_bps=upload_bps,
            enabled=data.enabled if data.enabled is not None else True,
        )

        # Apply limit via control engine (best effort)
        control_result = None
        try:
            control_result = control_engine.limit(
                device_id=device_id,
                ip=ip,
                download=data.download_limit,
                upload=data.upload_limit,
            )
        except Exception as control_error:
            control_result = {"error": str(control_error)}

        # Audit log
        log_admin_action(user["username"], "LIMITS", f"device:{device_id}", "none",
                        f"download={data.download_limit}KB/s, upload={data.upload_limit}KB/s, enabled={data.enabled}")

        return {
            "success": True,
            "device_id": device_id,
            "limit_id": limit_id,
            "download_limit_bps": download_bps,
            "upload_limit_bps": upload_bps,
            "enabled": data.enabled if data.enabled is not None else True,
            "control": control_result,
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set device limit: {error}",
        )

@router.post("/{device_id}/quota")
def quota_device(
    device_id: str,
    data: DeviceQuotaRequest,
    user=Depends(require_permission("control:quotas:write")),
):
    """Set or update quota for a device and persist to database."""

    try:
        repo = DeviceRepository()

        # Convert MB to bytes
        daily_bytes = None
        weekly_bytes = None
        monthly_bytes = None

        if data.daily_quota_mb is not None:
            daily_bytes = int(data.daily_quota_mb * 1024 * 1024)
        if data.weekly_quota_mb is not None:
            weekly_bytes = int(data.weekly_quota_mb * 1024 * 1024)
        if data.monthly_quota_mb is not None:
            monthly_bytes = int(data.monthly_quota_mb * 1024 * 1024)
        if data.quota_bytes is not None:
            daily_bytes = data.quota_bytes

        # Determine reset period
        reset_period = data.reset_period or "DAILY"
        if daily_bytes is None and weekly_bytes is not None:
            reset_period = "WEEKLY"
        elif daily_bytes is None and weekly_bytes is None and monthly_bytes is not None:
            reset_period = "MONTHLY"

        reset_day = data.reset_day or 1
        action = data.action or "ALERT"

        quota_id = repo.save_device_quota(
            device_id=device_id,
            daily_quota_bytes=daily_bytes,
            weekly_quota_bytes=weekly_bytes,
            monthly_quota_bytes=monthly_bytes,
            reset_period=reset_period,
            reset_day=reset_day,
            action=action,
            enabled=data.enabled if data.enabled is not None else True,
        )

        # Audit log
        log_admin_action(user["username"], "QUOTAS", f"device:{device_id}", "none",
                        f"daily={data.daily_quota_mb}MB, weekly={data.weekly_quota_mb}MB, monthly={data.monthly_quota_mb}MB, action={action}, enabled={data.enabled}")

        return {
            "success": True,
            "device_id": device_id,
            "quota_id": quota_id,
            "daily_quota_bytes": daily_bytes,
            "weekly_quota_bytes": weekly_bytes,
            "monthly_quota_bytes": monthly_bytes,
            "reset_period": reset_period,
            "reset_day": reset_day,
            "action": action,
            "enabled": data.enabled if data.enabled is not None else True,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set device quota: {error}",
        )

@router.post("/{device_id}/name")
def rename_device(
    device_id: str,
    data: DeviceNameRequest,
    user=Depends(
        require_roles(
            "ADMIN",
            "OPERATOR",
        )
    ),
):
    """Rename a device - persists custom name to database"""
    connection = get_connection()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE devices 
                SET custom_name = %s
                WHERE device_id = %s
                RETURNING device_id, custom_name
                """,
                (data.name, device_id)
            )
            row = cursor.fetchone()
            
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Device not found"
                )
            
        connection.commit()
        
        return {
            "success": True,
            "device_id": row[0],
            "name": row[1],
        }
    
    except HTTPException:
        raise
    
    except Exception as error:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rename device: {error}",
        )
    
    finally:
        return_connection(connection)

@router.post("/{device_id}/pause")
def pause_device(
    device_id: str,
    ip: str,
    user=Depends(
        require_roles(
            "ADMIN",
            "OPERATOR",
        )
    ),
):

    return control_engine.pause(
        device_id,
        ip,
    )

@router.post("/{device_id}/resume")
def resume_device(
    device_id: str,
    user=Depends(
        require_roles(
            "ADMIN",
            "OPERATOR",
        )
    ),
):

    return control_engine.resume(
        device_id
    )


# ============================================================
# DEVICE INTELLIGENCE ENDPOINTS
# ============================================================

from database.repository import DeviceIntelligenceRepository

intel_repo = DeviceIntelligenceRepository()

def _parse_time_range(range_str: str, start: str = None, end: str = None) -> int:
    """Parse time range string to hours"""
    if range_str == "custom" and start and end:
        # Calculate hours between start and end
        from datetime import datetime
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        return int((end_dt - start_dt).total_seconds() / 3600) + 1
    
    ranges = {
        "1h": 1,
        "24h": 24,
        "7d": 168,
        "30d": 720,
        "today": 24,
        "yesterday": 24,
    }
    return ranges.get(range_str, 24)


@router.get("/{device_id}/intelligence")
def get_device_intelligence(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None, description="Start time for custom range (ISO format)"),
    end: Optional[str] = Query(default=None, description="End time for custom range (ISO format)"),
    user=Depends(get_current_user),
):
    """
    Get comprehensive device intelligence summary.
    
    Returns:
    - Top Applications (with confidence levels)
    - Top Domains
    - Top Categories
    - Top Protocols
    - Peak Usage
    - Activity Timeline
    - Total Download/Upload
    - Usage Percentage
    """
    hours = _parse_time_range(range, start, end)
    
    try:
        summary = intel_repo.get_device_intelligence_summary(device_id, hours)
        return summary
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load device intelligence: {error}",
        )


@router.get("/{device_id}/applications")
def get_device_applications(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """
    Get application usage for a device with confidence levels.
    
    Each application includes:
    - Application name
    - Category
    - Confidence (HIGH/MEDIUM/LOW)
    - Download/Upload/Total bytes
    - Connections count
    """
    hours = _parse_time_range(range, start, end)
    
    try:
        apps = intel_repo.get_device_app_usage(device_id, hours)
        return apps
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load application usage: {error}",
        )


@router.get("/{device_id}/domains")
def get_device_domains(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    user=Depends(get_current_user),
):
    """
    Get domain usage for a device.
    
    Each domain includes:
    - Domain name
    - Category
    - Download/Upload/Total bytes
    - Query count
    - Connections count
    """
    hours = _parse_time_range(range, start, end)
    
    try:
        domains = intel_repo.get_device_domain_usage(device_id, hours, limit)
        return domains
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load domain usage: {error}",
        )


@router.get("/{device_id}/categories")
def get_device_categories(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """
    Get category usage for a device.
    
    Each category includes:
    - Category name
    - Download/Upload/Total bytes
    - Connections count
    """
    hours = _parse_time_range(range, start, end)
    
    try:
        categories = intel_repo.get_device_category_usage(device_id, hours)
        return categories
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load category usage: {error}",
        )
@router.get("/{device_id}/top-applications")
def get_device_top_applications(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    limit: int = Query(default=10, description="Number of top applications to return"),
    user=Depends(get_current_user),
):
    """
    Get top applications by traffic for a device.

    Returns a list of applications ranked by total traffic (download + upload), each including:
    - Application name
    - Category
    - Confidence
    - Download bytes
    - Upload bytes
    - Total bytes
    - Connections count
    - Evidence (top evidence by traffic)
    """
    hours = _parse_time_range(range, start, end)

    try:
        apps = intel_repo.get_device_app_usage(device_id, hours)
        # Apply limit
        if limit > 0:
            apps = apps[:limit]
        return apps
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load top applications: {error}",
        )


@router.get("/{device_id}/protocols")
def get_device_protocols(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """
    Get protocol usage for a device.
    
    Each protocol includes:
    - Protocol name
    - Download/Upload/Total bytes
    - Packet count
    - Connections count
    """
    hours = _parse_time_range(range, start, end)
    
    try:
        protocols = intel_repo.get_device_protocol_usage(device_id, hours)
        return protocols
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load protocol usage: {error}",
        )


@router.get("/{device_id}/peaks")
def get_device_peaks(
    device_id: str,
    days: int = Query(default=30, le=365),
    user=Depends(get_current_user),
):
    """
    Get peak usage for a device.
    
    Returns peak values for:
    - Download speed
    - Upload speed
    - Total speed
    - Connections
    With timestamp and day/hour breakdown.
    """
    try:
        peaks = intel_repo.get_device_peaks(device_id, days)
        return peaks
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load peaks: {error}",
        )


@router.get("/{device_id}/activity")
def get_device_activity(
    device_id: str,
    days: int = Query(default=7, le=365),
    user=Depends(get_current_user),
):
    """
    Get device activity timeline.
    
    Returns hourly activity for the specified period:
    - Hour start timestamp
    - Active status (boolean)
    - Total bytes
    - Connections count
    """
    try:
        activity = intel_repo.get_device_activity_timeline(device_id, days)
        return activity
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load activity timeline: {error}",
        )


@router.get("/{device_id}/sni")
def get_device_sni(
    device_id: str,
    range: str = Query(default="24h", description="Time range: 1h, 24h, 7d, 30d, custom"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """
    Get SNI (TLS Server Name Indication) observations for a device.
    
    This provides evidence for application attribution.
    Each observation includes:
    - SNI hostname
    - Destination IP
    - Destination port
    - Observed timestamp
    - Bytes transferred
    """
    hours = _parse_time_range(range, start, end)
    
    try:
        sni_obs = intel_repo.get_device_sni_observations(device_id, hours)
        return sni_obs
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load SNI observations: {error}",
        )
