"""Rebuild usage_monthly strictly from the canonical usage_daily ledger.

Root cause: the legacy inflated write path populated usage_monthly (and hourly)
for months where usage_daily had already been wiped/deleted by the identity
cleanup, leaving orphaned stale monthly rows (e.g. Aug upload=4854/packets=228
for dev_002 with no corresponding Aug usage_daily, or dev_009's 16MB/123MB
aggregates). /api/analytics/monthly then displayed those fake numbers.

This script deletes ALL usage_monthly rows and re-derives them strictly from
usage_daily, so every month shown by the monthly chart equals the verified
daily ledger. Idempotent and safe.
"""
import sys

sys.path.insert(0, ".")
from database.connection import get_connection, return_connection


def run(cur, sql, params=None):
    cur.execute(sql, params)


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1) Show orphans BEFORE: monthly rows with no matching daily row.
            cur.execute(
                """
                SELECT m.device_id, m.month_start, m.download_bytes, m.upload_bytes, m.packets
                FROM usage_monthly m
                LEFT JOIN (
                    SELECT device_id, DATE_TRUNC('month', day_start)::date AS mstart,
                           SUM(download_bytes) AS dl, SUM(upload_bytes) AS ul, SUM(packets) AS pk
                    FROM usage_daily
                    GROUP BY 1, 2
                ) d ON d.device_id = m.device_id AND d.mstart = m.month_start
                WHERE d.device_id IS NULL
                ORDER BY m.month_start DESC
                """
            )
            orphans = cur.fetchall()
            print("ORPHAN monthly rows (no matching usage_daily):")
            for r in orphans:
                print("  ", r)

            # 2) Full rebuild: delete ALL monthly, re-aggregate strictly from usage_daily.
            cur.execute("DELETE FROM usage_monthly")
            print(f"deleted all usage_monthly rows ({cur.rowcount})")
            cur.execute(
                """
                INSERT INTO usage_monthly (device_id, month_start, download_bytes, upload_bytes, packets, connections)
                SELECT device_id, DATE_TRUNC('month', day_start)::date,
                       SUM(download_bytes), SUM(upload_bytes), SUM(packets), NULL
                FROM usage_daily
                GROUP BY 1, 2
                """
            )
            print(f"re-aggregated usage_monthly from usage_daily: {cur.rowcount} rows")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("ERROR:", e)
        return 1
    finally:
        return_connection(conn)

    # 3) Verify: no orphans remain, and monthly == daily for every overlap.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.device_id, m.month_start, m.download_bytes, m.upload_bytes, m.packets
                FROM usage_monthly m
                LEFT JOIN (
                    SELECT device_id, DATE_TRUNC('month', day_start)::date AS mstart
                    FROM usage_daily
                    GROUP BY 1, 2
                ) d ON d.device_id = m.device_id AND d.mstart = m.month_start
                WHERE d.device_id IS NULL
                """
            )
            print("ORPHANS after rebuild:", cur.fetchall() or "NONE")

            cur.execute(
                """
                SELECT m.device_id, m.month_start, m.download_bytes, m.upload_bytes
                FROM usage_monthly m
                JOIN (
                    SELECT device_id, DATE_TRUNC('month', day_start)::date AS mstart,
                           SUM(download_bytes) AS dl, SUM(upload_bytes) AS ul
                    FROM usage_daily
                    GROUP BY 1, 2
                ) d ON d.device_id = m.device_id AND d.mstart = m.month_start
                WHERE m.download_bytes <> d.dl OR m.upload_bytes <> d.ul
                """
            )
            print("MISMATCHES after rebuild:", cur.fetchall() or "NONE - all consistent")
    finally:
        return_connection(conn)
    return 0


if __name__ == "__main__":
    sys.exit(main())