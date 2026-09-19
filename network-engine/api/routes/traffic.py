import traceback
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from database.connection import get_connection, return_connection
from api.security import get_current_user

router = APIRouter()


@router.get("/recent")
def recent_traffic(
    device_id: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            if device_id:
                cursor.execute(
                    """
                    SELECT
                        t.device_id::text AS device_id,
                        COALESCE(split_part(d.ip_address::text, '/', 1), '') AS ip,
                        t.sampled_at::text AS time,
                        COALESCE(t.download_bytes, 0) AS download,
                        COALESCE(t.upload_bytes, 0) AS upload,
                        COALESCE(t.packets, 0) AS packets,
                        COALESCE(t.connections, 0) AS connections,
                        COALESCE(t.download_speed_bps, 0) AS download_speed_bps,
                        COALESCE(t.upload_speed_bps, 0) AS upload_speed_bps
                    FROM traffic_samples t
                    LEFT JOIN devices d
                        ON d.device_id::text = t.device_id::text
                    WHERE t.device_id::text = %s
                    ORDER BY
                        t.sampled_at DESC
                    LIMIT 100
                    """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        t.device_id::text AS device_id,
                        COALESCE(split_part(d.ip_address::text, '/', 1), '') AS ip,
                        t.sampled_at::text AS time,
                        COALESCE(t.download_bytes, 0) AS download,
                        COALESCE(t.upload_bytes, 0) AS upload,
                        COALESCE(t.packets, 0) AS packets,
                        COALESCE(t.connections, 0) AS connections,
                        COALESCE(t.download_speed_bps, 0) AS download_speed_bps,
                        COALESCE(t.upload_speed_bps, 0) AS upload_speed_bps
                    FROM traffic_samples t
                    LEFT JOIN devices d
                        ON d.device_id::text = t.device_id::text
                    ORDER BY
                        t.sampled_at DESC
                    LIMIT 100
                    """
                )

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [
                row if isinstance(row, dict) else dict(zip(columns, row))
                for row in rows
            ]

    except Exception as e:
        print("\n" + "=" * 50)
        print("[Traffic Query Error Details]:")
        traceback.print_exc()
        print("=" * 50 + "\n")

        raise HTTPException(
            status_code=500,
            detail=f"Database query error: {str(e)}"
        )

    finally:
        return_connection(connection)


@router.get("/history")
def traffic_history(
    device_id: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    user=Depends(get_current_user),
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            if device_id:
                cursor.execute(
                    """
                    SELECT
                        DATE(sampled_at) AS date,
                        SUM(download_bytes) AS download,
                        SUM(upload_bytes) AS upload,
                        SUM(download_bytes + upload_bytes) AS total,
                        SUM(packets) AS packets
                    FROM traffic_samples
                    WHERE device_id::text = %s
                      AND sampled_at >= NOW() - %s
                    GROUP BY DATE(sampled_at)
                    ORDER BY DATE(sampled_at) ASC
                    """,
                    (device_id, timedelta(days=days)),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        DATE(sampled_at) AS date,
                        SUM(download_bytes) AS download,
                        SUM(upload_bytes) AS upload,
                        SUM(download_bytes + upload_bytes) AS total,
                        SUM(packets) AS packets
                    FROM traffic_samples
                    WHERE sampled_at >= NOW() - %s
                    GROUP BY DATE(sampled_at)
                    ORDER BY DATE(sampled_at) ASC
                    """,
                    (timedelta(days=days),),
                )

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [
                row if isinstance(row, dict) else dict(zip(columns, row))
                for row in rows
            ]

    except Exception as e:
        print("\n" + "=" * 50)
        print("[Traffic History Query Error Details]:")
        traceback.print_exc()
        print("=" * 50 + "\n")

        raise HTTPException(
            status_code=500,
            detail=f"Database query error: {str(e)}"
        )

    finally:
        return_connection(connection)
