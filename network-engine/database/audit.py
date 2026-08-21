from database.connection import get_connection


def write_audit_log(
    username,
    action,
    target=None,
    details=None,
):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO events (
                    event_type,
                    source,
                    message
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    "AUDIT",
                    username,
                    f"{action}: {target} {details or ''}",
                ),
            )

        connection.commit()

    finally:

        connection.close()