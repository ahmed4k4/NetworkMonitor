import json
from database.connection import get_connection, return_connection
from datetime import datetime


def write_audit_log(
    username: str,
    action: str,
    target: str = None,
    old_value: str = None,
    new_value: str = None,
    result: str = "SUCCESS",
    details: str = None,
    device_id: str = None,
):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO audit_logs (
                    event_type,
                    message,
                    user_id,
                    device_id,
                    metadata,
                    created_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    action,
                    details or f"{action} on {target}",
                    username,
                    device_id,
                    json.dumps({
                        "old_value": old_value,
                        "new_value": new_value,
                        "result": result,
                        "details": details
                    }),
                    datetime.now(),
                ),
            )

        connection.commit()

    finally:

        return_connection(connection)


def log_admin_action(
    username: str,
    action: str,
    target: str,
    old_value: str = None,
    new_value: str = None,
    result: str = "SUCCESS",
    details: str = None,
    device_id: str = None,
):
    """Log administrative actions with full context for audit trail"""
    # Use explicit device_id if provided, otherwise extract from target if it's a device target
    if device_id is None and target and target.startswith("device:"):
        device_id = target.split(":", 1)[1]
    write_audit_log(username, action, target, old_value, new_value, result, details, device_id)
