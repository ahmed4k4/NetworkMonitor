from fastapi import APIRouter

from database.connection import get_connection, return_connection


router = APIRouter()


@router.get("/")
def applications():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    name,
                    category,
                    first_seen,
                    last_seen
                FROM applications
                ORDER BY last_seen DESC
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "name": row[0],
                "category": row[1],
                "first_seen": row[2],
                "last_seen": row[3],
            }
            for row in rows
        ]

    finally:

        return_connection(connection)