from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from control.engine import ControlEngine

from api.security import (
    get_current_user,
    require_roles,
)

from database.connection import (
    get_connection,
)

from database.repository import DeviceRepository

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
    reset_day: Optional[int] = 1
    enabled: Optional[bool] = True


class DeviceNameRequest(BaseModel):
    name: str
    custom_name: Optional[str] = None
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
                    dl.used_bytes,
                    dl.enabled AS quota_enabled
                FROM devices d
                LEFT JOIN usage_daily ud
                    ON ud.device_id = d.device_id
                    AND ud.day_start = CURRENT_DATE
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
                """
            )

            rows = cursor.fetchall()

        devices = []

        for row in rows:
            download_today = row[11] or 0
            upload_today = row[12] or 0
            download_speed = row[13] or 0
            upload_speed = row[14] or 0
            # Columns: 15=limit_id, 16=dl_limit, 17=ul_limit, 18=limit_enabled,
            # 19=quota_id, 20=daily_quota, 21=weekly_quota, 22=monthly_quota,
            # 23=used_bytes, 24=quota_enabled
            quota_bytes = row[20] or row[21] or row[22]
            used_bytes = row[23] or 0
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
                    "vendor": row[4],
                    "interface": row[5],
                    "state": row[6],
                    "first_seen": row[7],
                    "last_seen": row[8],
                    "upload": row[9] or 0,
                    "download": row[10] or 0,
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
                    "quota_enabled": row[24],
                    "limit_id": row[15],
                    "download_limit_bps": row[16],
                    "upload_limit_bps": row[17],
                    "limit_enabled": bool(row[18]) if row[18] is not None else False,
                }
            )

        return devices

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load devices: {error}",
        )

    finally:

        connection.close()


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
                    dl.used_bytes,
                    dl.enabled AS quota_enabled
                FROM devices d
                LEFT JOIN usage_daily ud
                    ON ud.device_id = d.device_id
                    AND ud.day_start = CURRENT_DATE
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
                (device_id,),
            )

            row = cursor.fetchone()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Device not found",
            )

        download_today = row[11] or 0
        upload_today = row[12] or 0
        download_speed = row[13] or 0
        upload_speed = row[14] or 0
        quota_bytes = row[20] or row[21] or row[22]
        used_bytes = row[23] or 0
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
            "vendor": row[4],
            "interface": row[5],
            "state": row[6],
            "first_seen": row[7],
            "last_seen": row[8],
            "upload": row[9] or 0,
            "download": row[10] or 0,
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
            "quota_enabled": row[24],
            "limit_id": row[15],
            "download_limit_bps": row[16],
            "upload_limit_bps": row[17],
            "limit_enabled": bool(row[18]) if row[18] is not None else False,
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

        connection.close()


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
            "vendor": row[4],
            "interface": row[5],
            "state": row[6],
            "first_seen": row[7],
            "last_seen": row[8],
            "upload": row[9] or 0,
            "download": row[10] or 0,
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to find device: {error}",
        )

    finally:

        connection.close()

@router.post("/{device_id}/block")
def block_device(
    device_id: str,
    ip: str,
    user=Depends(
        require_roles(
            "Admin",
            "Operator",
        )
    ),
):

    result = control_engine.block(
        device_id,
        ip,
    )

    return result

@router.post("/{device_id}/unblock")
def unblock_device(
    device_id: str,
    user=Depends(
        require_roles(
            "Admin",
            "Operator",
        )
    ),
):

    return control_engine.unblock(
        device_id
    )

@router.post("/{device_id}/limit")
def limit_device(
    device_id: str,
    ip: str,
    data: DeviceLimitRequest,
    user=Depends(
        require_roles(
            "Admin",
            "Operator",
        )
    ),
):
    """Set or update speed limits for a device and persist to database."""
    try:
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
    user=Depends(
        require_roles(
            "Admin",
            "Operator",
        )
    ),
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
        reset_period = "DAILY"
        if daily_bytes is None and weekly_bytes is not None:
            reset_period = "WEEKLY"
        elif daily_bytes is None and weekly_bytes is None and monthly_bytes is not None:
            reset_period = "MONTHLY"

        quota_id = repo.save_device_quota(
            device_id=device_id,
            daily_quota_bytes=daily_bytes,
            weekly_quota_bytes=weekly_bytes,
            monthly_quota_bytes=monthly_bytes,
            reset_period=reset_period,
            enabled=data.enabled if data.enabled is not None else True,
        )

        return {
            "success": True,
            "device_id": device_id,
            "quota_id": quota_id,
            "daily_quota_bytes": daily_bytes,
            "weekly_quota_bytes": weekly_bytes,
            "monthly_quota_bytes": monthly_bytes,
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
            "Admin",
            "Operator",
        )
    ),
):

    return {
        "success": True,
        "device_id": device_id,
        "name": data.name,
    }

@router.post("/{device_id}/pause")
def pause_device(
    device_id: str,
    ip: str,
    user=Depends(
        require_roles(
            "Admin",
            "Operator",
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
            "Admin",
            "Operator",
        )
    ),
):

    return control_engine.resume(
        device_id
    )