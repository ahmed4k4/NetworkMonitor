from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from database.connection import get_connection
from api.security import get_current_user

router = APIRouter()


@router.get("/top-devices")
def top_devices(user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    device_id,
                    ip_address::text,
                    total_upload,
                    total_download,
                    (
                        total_upload
                        + total_download
                    ) AS total
                FROM devices
                ORDER BY total DESC
                LIMIT 10
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "device_id": row[0],
                "ip": row[1],
                "upload": row[2],
                "download": row[3],
                "total": row[4],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load top devices: {error}")
    finally:
        connection.close()


@router.get("/hourly")
def hourly_analytics(
    device_id: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """Return hourly traffic analytics."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if device_id:
                cursor.execute(
                    """
                    SELECT
                        hour_start::text,
                        COALESCE(download_bytes, 0),
                        COALESCE(upload_bytes, 0),
                        COALESCE(packets, 0),
                        COALESCE(connections, 0)
                    FROM usage_hourly
                    WHERE device_id = %s
                    ORDER BY hour_start DESC
                    LIMIT 24
                    """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        hour_start::text,
                        SUM(COALESCE(download_bytes, 0)),
                        SUM(COALESCE(upload_bytes, 0)),
                        SUM(COALESCE(packets, 0)),
                        SUM(COALESCE(connections, 0))
                    FROM usage_hourly
                    WHERE hour_start > NOW() - INTERVAL '24 hours'
                    GROUP BY hour_start
                    ORDER BY hour_start DESC
                    LIMIT 24
                    """
                )
            rows = cursor.fetchall()
        return [
            {
                "time": row[0],
                "download": row[1],
                "upload": row[2],
                "packets": row[3],
                "connections": row[4],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load hourly analytics: {error}")
    finally:
        connection.close()


@router.get("/daily")
def daily_analytics(
    device_id: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """Return daily traffic analytics."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if device_id:
                cursor.execute(
                    """
                    SELECT
                        day_start::text,
                        COALESCE(download_bytes, 0),
                        COALESCE(upload_bytes, 0),
                        COALESCE(packets, 0),
                        COALESCE(connections, 0)
                    FROM usage_daily
                    WHERE device_id = %s
                    ORDER BY day_start DESC
                    LIMIT 30
                    """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        day_start::text,
                        SUM(COALESCE(download_bytes, 0)),
                        SUM(COALESCE(upload_bytes, 0)),
                        SUM(COALESCE(packets, 0)),
                        SUM(COALESCE(connections, 0))
                    FROM usage_daily
                    WHERE day_start > NOW() - INTERVAL '30 days'
                    GROUP BY day_start
                    ORDER BY day_start DESC
                    LIMIT 30
                    """
                )
            rows = cursor.fetchall()
        return [
            {
                "time": row[0],
                "download": row[1],
                "upload": row[2],
                "packets": row[3],
                "connections": row[4],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load daily analytics: {error}")
    finally:
        connection.close()


@router.get("/weekly")
def weekly_analytics(
    device_id: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """Return weekly traffic analytics."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if device_id:
                cursor.execute(
                    """
                    SELECT
                        day_start::text,
                        COALESCE(download_bytes, 0),
                        COALESCE(upload_bytes, 0),
                        COALESCE(packets, 0),
                        COALESCE(connections, 0)
                    FROM usage_daily
                    WHERE device_id = %s
                    ORDER BY day_start DESC
                    LIMIT 7
                    """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        day_start::text,
                        SUM(COALESCE(download_bytes, 0)),
                        SUM(COALESCE(upload_bytes, 0)),
                        SUM(COALESCE(packets, 0)),
                        SUM(COALESCE(connections, 0))
                    FROM usage_daily
                    WHERE day_start > NOW() - INTERVAL '7 days'
                    GROUP BY day_start
                    ORDER BY day_start DESC
                    LIMIT 7
                    """
                )
            rows = cursor.fetchall()
        return [
            {
                "time": row[0],
                "download": row[1],
                "upload": row[2],
                "packets": row[3],
                "connections": row[4],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load weekly analytics: {error}")
    finally:
        connection.close()


@router.get("/monthly")
def monthly_analytics(
    device_id: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    """Return monthly traffic analytics."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if device_id:
                cursor.execute(
                    """
                    SELECT
                        month_start::text,
                        COALESCE(download_bytes, 0),
                        COALESCE(upload_bytes, 0),
                        COALESCE(packets, 0),
                        COALESCE(connections, 0)
                    FROM usage_monthly
                    WHERE device_id = %s
                    ORDER BY month_start DESC
                    LIMIT 12
                    """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        month_start::text,
                        SUM(COALESCE(download_bytes, 0)),
                        SUM(COALESCE(upload_bytes, 0)),
                        SUM(COALESCE(packets, 0)),
                        SUM(COALESCE(connections, 0))
                    FROM usage_monthly
                    WHERE month_start > NOW() - INTERVAL '12 months'
                    GROUP BY month_start
                    ORDER BY month_start DESC
                    LIMIT 12
                    """
                )
            rows = cursor.fetchall()
        return [
            {
                "time": row[0],
                "download": row[1],
                "upload": row[2],
                "packets": row[3],
                "connections": row[4],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load monthly analytics: {error}")
    finally:
        connection.close()


@router.get("/protocols")
def protocol_analytics(user=Depends(get_current_user)):
    """Return protocol statistics from flows."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    protocol,
                    SUM(packets),
                    SUM(bytes),
                    COUNT(*)
                FROM flows
                WHERE state = 'ACTIVE'
                GROUP BY protocol
                ORDER BY SUM(bytes) DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "protocol": row[0],
                "packets": row[1],
                "bytes": row[2],
                "connections": row[3],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load protocol analytics: {error}")
    finally:
        connection.close()


@router.get("/domains")
def domain_analytics(user=Depends(get_current_user)):
    """Return domain analytics with query counts and traffic."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    q.domain,
                    COUNT(*) as queries,
                    COUNT(DISTINCT q.device_id) as devices,
                    MAX(q.queried_at)::text as last_seen
                FROM dns_queries q
                GROUP BY q.domain
                ORDER BY queries DESC
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "domain": row[0],
                "queries": row[1],
                "devices": row[2],
                "traffic": 0,
                "last_seen": row[3],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load domain analytics: {error}")
    finally:
        connection.close()


@router.get("/applications")
def application_analytics(user=Depends(get_current_user)):
    """Return application analytics with traffic data."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.name,
                    a.category,
                    COUNT(DISTINCT d.device_id) as devices,
                    SUM(COALESCE(f.bytes, 0)) as traffic,
                    a.last_seen::text
                FROM applications a
                LEFT JOIN flows f ON f.device_id = a.name
                LEFT JOIN devices d ON d.device_id = f.device_id
                GROUP BY a.name, a.category, a.last_seen
                ORDER BY traffic DESC NULLS LAST
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "name": row[0],
                "category": row[1],
                "devices": row[2],
                "traffic": row[3] or 0,
                "connections": 0,
                "percentage": 0,
                "first_seen": row[4],
                "last_seen": row[4],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load application analytics: {error}")
    finally:
        connection.close()
