from database.connection import get_connection, return_connection
from config import network_config as config


def aggregate_hourly():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO usage_hourly (
                    device_id,
                    hour_start,
                    download_bytes,
                    upload_bytes,
                    packets,
                    connections
                )

                SELECT
                    device_id,

                    date_trunc(
                        'hour',
                        sampled_at AT TIME ZONE %s
                    ) AS hour_start,

                    SUM(download_bytes),

                    SUM(upload_bytes),

                    SUM(packets),

                    SUM(connections)

                FROM traffic_samples

                WHERE sampled_at >= (NOW() AT TIME ZONE %s) - INTERVAL '2 hours'

                GROUP BY
                    device_id,
                    hour_start

                ON CONFLICT (
                    device_id,
                    hour_start
                )

                DO UPDATE SET

                    download_bytes =
                        EXCLUDED.download_bytes,

                    upload_bytes =
                        EXCLUDED.upload_bytes,

                    packets =
                        EXCLUDED.packets,

                    connections =
                        EXCLUDED.connections
                """,
                (config.tz, config.tz)
            )

        connection.commit()

    finally:
        return_connection(connection)


def aggregate_daily():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO usage_daily (
                    device_id,
                    day_start,
                    download_bytes,
                    upload_bytes,
                    packets,
                    connections
                )

                SELECT
                    device_id,

                    (sampled_at AT TIME ZONE %s)::DATE AS day_start,

                    SUM(download_bytes),

                    SUM(upload_bytes),

                    SUM(packets),

                    SUM(connections)

                FROM traffic_samples

                WHERE sampled_at >= (NOW() AT TIME ZONE %s) - INTERVAL '2 days'

                GROUP BY
                    device_id,
                    day_start

                ON CONFLICT (
                    device_id,
                    day_start
                )

                DO UPDATE SET

                    download_bytes =
                        EXCLUDED.download_bytes,

                    upload_bytes =
                        EXCLUDED.upload_bytes,

                    packets =
                        EXCLUDED.packets,

                    connections =
                        EXCLUDED.connections
                """,
                (config.tz, config.tz)
            )

        connection.commit()

    finally:
        return_connection(connection)

def aggregate_monthly():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO usage_monthly (
                    device_id,
                    month_start,
                    download_bytes,
                    upload_bytes,
                    packets,
                    connections
                )

                SELECT
                    device_id,

                    DATE_TRUNC(
                        'month',
                        day_start
                    )::DATE,

                    SUM(download_bytes),

                    SUM(upload_bytes),

                    SUM(packets),

                    SUM(connections)

                FROM usage_daily

                GROUP BY
                    device_id,
                    DATE_TRUNC(
                        'month',
                        day_start
                    )

                ON CONFLICT (
                    device_id,
                    month_start
                )

                DO UPDATE SET

                    download_bytes =
                        EXCLUDED.download_bytes,

                    upload_bytes =
                        EXCLUDED.upload_bytes,

                    packets =
                        EXCLUDED.packets,

                    connections =
                        EXCLUDED.connections
                """
            )

        connection.commit()

    finally:
        return_connection(connection)
