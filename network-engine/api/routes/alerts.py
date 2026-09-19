from fastapi import APIRouter, Depends, HTTPException

from database.connection import get_connection, return_connection
from api.security import get_current_user

router = APIRouter()


@router.get("/")
def get_alerts(
    user=Depends(get_current_user),
):
    """
    Return all alerts from the database.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    device_id,
                    alert_type,
                    severity,
                    message,
                    resolved,
                    created_at,
                    resolved_at
                FROM alerts
                ORDER BY created_at DESC
                LIMIT 200
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "device_id": row[1],
                "type": row[2],
                "severity": row[3],
                "message": row[4],
                "resolved": row[5],
                "created_at": row[6],
                "resolved_at": row[7],
            }
            for row in rows
        ]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load alerts: {error}",
        )

    finally:
        return_connection(connection)
