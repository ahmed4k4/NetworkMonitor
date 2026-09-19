from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from database.connection import get_connection, return_connection
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
        return_connection(connection)


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
        return_connection(connection)


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
                    WHERE day_start > (NOW() AT TIME ZONE 'Africa/Cairo')::date - INTERVAL '30 days'
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
        return_connection(connection)


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
                    WHERE day_start > (NOW() AT TIME ZONE 'Africa/Cairo')::date - INTERVAL '7 days'
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
        return_connection(connection)


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
        return_connection(connection)


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
        return_connection(connection)


@router.get("/domains")
def domain_analytics(user=Depends(get_current_user)):
    """Return domain analytics with query counts and traffic from attributed usage."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    domain,
                    SUM(queries) as queries,
                    COUNT(DISTINCT device_id) as devices,
                    MAX(hour_start)::text as last_seen,
                    SUM(total_bytes) as traffic
                FROM device_domain_usage
                WHERE hour_start > NOW() - INTERVAL '24 hours'
                GROUP BY domain
                ORDER BY traffic DESC
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "domain": row[0],
                "queries": row[1],
                "devices": row[2],
                "traffic": row[4],
                "last_seen": row[3],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load domain analytics: {error}")
    finally:
        return_connection(connection)


@router.get("/applications")
def application_analytics(user=Depends(get_current_user)):
    """Return application analytics with traffic data from attributed usage."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    application as name,
                    category,
                    COUNT(DISTINCT device_id) as devices,
                    SUM(total_bytes) as traffic,
                    SUM(connections) as connections,
                    MIN(hour_start)::text as first_seen,
                    MAX(hour_start)::text as last_seen
                FROM device_app_usage
                WHERE hour_start > NOW() - INTERVAL '24 hours'
                GROUP BY application, category
                ORDER BY traffic DESC
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
        
        # Calculate total traffic for percentage
        total_traffic = sum(row[3] or 0 for row in rows)
        
        return [
            {
                "name": row[0],
                "category": row[1],
                "devices": row[2],
                "traffic": row[3] or 0,
                "connections": row[4] or 0,
                "percentage": round((row[3] or 0) / total_traffic * 100, 1) if total_traffic > 0 else 0,
                "first_seen": row[5],
                "last_seen": row[6],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load application analytics: {error}")
    finally:
        return_connection(connection)
