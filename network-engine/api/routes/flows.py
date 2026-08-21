from fastapi import APIRouter

from database.connection import get_connection


router = APIRouter()


@router.get("/active")
def active_flows():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    device_id,
                    source_ip,
                    destination_ip,
                    source_port,
                    destination_port,
                    protocol,
                    packets,
                    bytes,
                    upload_bytes,
                    download_bytes,
                    direction,
                    started_at,
                    last_seen,
                    state
                FROM flows

                ORDER BY last_seen DESC

                LIMIT 500
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "device_id": row[1],
                "source_ip": str(row[2]).split('/')[0] if row[2] else None,
                "destination_ip": str(row[3]).split('/')[0] if row[3] else None,
                "source_port": row[4],
                "destination_port": row[5],
                "protocol": row[6],
                "packets": row[7],
                "bytes": row[8],
                "upload": row[9],
                "download": row[10],
                "direction": row[11],
                "started_at": row[12],
                "last_seen": row[13],
                "state": row[14],
            }
            for row in rows
        ]

    finally:

        connection.close()
