from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database.connection import get_connection, return_connection
from api.security import get_current_user

router = APIRouter()


class ReportRequest(BaseModel):
    type: str = "DAILY"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.get("/")
def get_reports(
    user=Depends(get_current_user),
):
    """
    Return all generated reports from the audit_logs table.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    event_type,
                    message,
                    created_at
                FROM audit_logs
                WHERE event_type IN ('REPORT_GENERATED', 'REPORT')
                ORDER BY created_at DESC
                LIMIT 100
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "type": row[1],
                "message": row[2],
                "created_at": row[3],
                "period_start": row[3],
                "period_end": row[3],
                "status": "COMPLETED",
                "file_url": None,
            }
            for row in rows
        ]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load reports: {error}",
        )

    finally:
        return_connection(connection)


@router.post("/generate")
def generate_report(
    params: ReportRequest,
    user=Depends(get_current_user),
):
    """
    Generate a new report.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_logs (event_type, message, user_id, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id, created_at
                """,
                (
                    "REPORT_GENERATED",
                    f"Generated {params.type} report",
                    user.get("username", "unknown"),
                ),
            )

            row = cursor.fetchone()
            connection.commit()

        return {
            "id": row[0],
            "type": params.type,
            "status": "COMPLETED",
            "period_start": params.start_date or "",
            "period_end": params.end_date or "",
            "created_at": row[1],
            "file_url": None,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {error}",
        )

    finally:
        return_connection(connection)
