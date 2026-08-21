from database.connection import get_connection


def cleanup_old_data():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            # Raw flows: 7 days

            cursor.execute(
                """
                DELETE FROM flows
                WHERE last_seen <
                    NOW() - INTERVAL '7 days'
                """
            )

            # Traffic samples: 90 days

            cursor.execute(
                """
                DELETE FROM traffic_samples
                WHERE sampled_at <
                    NOW() - INTERVAL '90 days'
                """
            )

            # Hourly: 90 days

            cursor.execute(
                """
                DELETE FROM usage_hourly
                WHERE hour_start <
                    NOW() - INTERVAL '90 days'
                """
            )

            # Daily: 2 years

            cursor.execute(
                """
                DELETE FROM usage_daily
                WHERE day_start <
                    CURRENT_DATE - INTERVAL '2 years'
                """
            )

        connection.commit()

    finally:
        connection.close()