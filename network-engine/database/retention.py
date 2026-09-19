"""
Data Retention and Cleanup Module

This module implements data retention policies to prevent unbounded database growth
while preserving historical analytics data as required.

Retention Policies:
- Raw flow data: 7 days (detailed packet-level flows)
- Traffic samples: 30 days (1-second resolution samples)
- Hourly aggregated data: 90 days (device_app_usage, device_domain_usage, etc.)
- Daily aggregated data: 2 years (usage_daily)
- Monthly aggregated data: 5 years (usage_monthly)
- DNS queries: 30 days
- SNI observations: 30 days
- Device peaks: 1 year
- Device activity timeline: 1 year
- Audit logs: 1 year
- Alerts: 1 year
- Events: 30 days
"""

from database.connection import get_connection, get_pool, return_connection
from logger import logger
from datetime import datetime, timedelta
import time


# Retention policies in days
RETENTION_POLICIES = {
    # Raw data - short retention
    "flows": 7,
    "traffic_samples": 30,
    "dns_queries": 30,
    "sni_observations": 30,
    "connections": 30,
    "events": 30,
    
    # Hourly aggregates - medium retention
    "device_app_usage": 90,
    "device_domain_usage": 90,
    "device_category_usage": 90,
    "device_protocol_usage": 90,
    "usage_hourly": 90,
    "device_peaks": 365,
    "device_activity_timeline": 365,
    
    # Daily aggregates - long retention
    "usage_daily": 730,  # 2 years
    
    # Monthly aggregates - very long retention
    "usage_monthly": 1825,  # 5 years
    
    # System tables
    "audit_logs": 365,
    "alerts": 365,
}


def cleanup_old_data():
    """
    Clean up old data based on retention policies.
    Should be run periodically (e.g., daily via cron or scheduled task).
    """
    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                for table, retention_days in RETENTION_POLICIES.items():
                    if table in ("usage_daily", "usage_monthly"):
                        # These use DATE columns
                        time_column = "day_start" if table == "usage_daily" else "month_start"
                        cutoff = datetime.now().date() - timedelta(days=retention_days)
                        where_clause = f"{time_column} < %s"
                    elif table in ("device_peaks", "device_activity_timeline"):
                        # These use TIMESTAMPTZ columns
                        time_column = "peak_at" if table == "device_peaks" else "hour_start"
                        cutoff = datetime.now() - timedelta(days=retention_days)
                        where_clause = f"{time_column} < %s"
                    else:
                        # Most tables use TIMESTAMPTZ
                        if table in ("flows", "traffic_samples", "audit_logs", "alerts"):
                            time_column = "created_at" if table in ("audit_logs", "alerts") else "started_at" if table == "flows" else "sampled_at"
                        elif table == "dns_queries":
                            time_column = "queried_at"
                        elif table == "sni_observations":
                            time_column = "observed_at"
                        elif table == "connections":
                            time_column = "started_at"
                        elif table == "events":
                            time_column = "created_at"
                        else:
                            # Intelligence tables
                            time_column = "hour_start"
                        
                        cutoff = datetime.now() - timedelta(days=retention_days)
                        where_clause = f"{time_column} < %s"
                    
                    # Check if table exists first
                    cursor.execute("""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = %s
                    """, (table,))
                    
                    if cursor.fetchone():
                        try:
                            # Count rows to be deleted
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}", (cutoff,))
                            count = cursor.fetchone()[0]
                            
                            if count > 0:
                                # Delete in batches to avoid long locks
                                deleted_total = 0
                                batch_size = 10000
                                
                                while True:
                                    cursor.execute(f"""
                                        DELETE FROM {table}
                                        WHERE ctid IN (
                                            SELECT ctid FROM {table}
                                            WHERE {where_clause}
                                            LIMIT %s
                                        )
                                    """, (cutoff, batch_size))
                                    
                                    batch_deleted = cursor.rowcount
                                    deleted_total += batch_deleted
                                    connection.commit()
                                    
                                    if batch_deleted < batch_size:
                                        break
                                    
                                    # Small pause between batches
                                    time.sleep(0.1)
                                
                                logger.info(f"Retention cleanup: deleted {deleted_total} rows from {table} (older than {retention_days} days)")
                            else:
                                logger.debug(f"Retention cleanup: no rows to delete from {table}")
                        
                        except Exception as e:
                            logger.error(f"Error cleaning up {table}: {e}")
                            connection.rollback()
                    else:
                        logger.debug(f"Table {table} does not exist, skipping")
        
        except Exception as e:
            logger.error(f"Error in cleanup_old_data: {e}")
            connection.rollback()
        finally:
            return_connection(connection)


def get_table_sizes():
    """Get current table sizes for monitoring"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    relname as tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
                    pg_total_relation_size(schemaname||'.'||relname) as size_bytes,
                    n_live_tup as estimated_rows
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC
            """)
            rows = cursor.fetchall()
            
            for r in rows:
                logger.info(f"Table {r[1]}: size={r[2]} rows~={r[4]}")
            
            return rows


def vacuum_analyze():
    """Run VACUUM ANALYZE on all tables for optimal query planning"""
    with get_connection() as connection:
        try:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("VACUUM ANALYZE")
            logger.info("VACUUM ANALYZE completed")
        except Exception as e:
            logger.error(f"Error in vacuum_analyze: {e}")
        finally:
            return_connection(connection)


if __name__ == "__main__":
    logger.info("Starting data retention cleanup...")
    cleanup_old_data()
    get_table_sizes()
    vacuum_analyze()
    logger.info("Data retention cleanup completed")