from fastapi import APIRouter

from database.connection import get_connection


router = APIRouter()


@router.get("/recent")
def recent_dns():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    q.queried_at,
                    d.device_id,
                    q.domain,
                    q.query_type,
                    q.response_ip::text
                FROM dns_queries q

                LEFT JOIN devices d
                    ON d.device_id = q.device_id

                ORDER BY
                    q.queried_at DESC

                LIMIT 200
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "time": row[0],
                "device_id": row[1],
                "domain": row[2],
                "query_type": row[3],
                "response_ip": row[4],
            }
            for row in rows
        ]

    finally:

        connection.close()