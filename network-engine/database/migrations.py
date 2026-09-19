"""Idempotent database schema initialization (single source of truth).

All statements are additive and safe to run repeatedly (CREATE TABLE IF NOT
EXISTS / CREATE INDEX IF NOT EXISTS / ALTER TABLE ... ADD COLUMN IF NOT
EXISTS). This module MUST match the schema expected by `repository.py` and
the API layer exactly, so a fresh install gets the complete schema.

The actual production schema was captured in `schema_out.txt` (root dir);
this file is kept in sync with that dump.
"""

from logger import logger


MIGRATIONS = [
    # --- Core tables ---
    """
    CREATE TABLE IF NOT EXISTS devices (
        device_id       VARCHAR(64) PRIMARY KEY,
        mac_address     MACADDR UNIQUE,
        ip_address      INET,
        hostname        VARCHAR(255),
        vendor          VARCHAR(255),
        interface_name  VARCHAR(64),
        state           VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
        first_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        total_upload    BIGINT NOT NULL DEFAULT 0,
        total_download  BIGINT NOT NULL DEFAULT 0,
        total_packets   BIGINT NOT NULL DEFAULT 0,
        custom_name     VARCHAR(255)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS flows (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        source_ip          INET NOT NULL,
        destination_ip     INET NOT NULL,
        source_port        INTEGER,
        destination_port   INTEGER,
        protocol           VARCHAR(255),
        interface_name     VARCHAR(255),
        direction          VARCHAR(20),
        started_at         TIMESTAMPTZ NOT NULL,
        last_seen          TIMESTAMPTZ,
        duration_seconds   BIGINT DEFAULT 0,
        packets            BIGINT DEFAULT 0,
        bytes              BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        download_bytes     BIGINT DEFAULT 0,
        state              VARCHAR(32) DEFAULT 'ACTIVE'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS traffic_samples (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        sampled_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        download_bytes     BIGINT NOT NULL DEFAULT 0,
        upload_bytes       BIGINT NOT NULL DEFAULT 0,
        packets            BIGINT NOT NULL DEFAULT 0,
        connections        BIGINT NOT NULL DEFAULT 0,
        download_speed_bps BIGINT NOT NULL DEFAULT 0,
        upload_speed_bps   BIGINT NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS connections (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        source_ip          INET,
        destination_ip     INET,
        source_port        INTEGER,
        destination_port   INTEGER,
        protocol           VARCHAR(255),
        started_at         TIMESTAMPTZ,
        last_seen          TIMESTAMPTZ,
        closed_at          TIMESTAMPTZ,
        state              VARCHAR(32)
    )
    """,
    # --- Intelligence tables ---
    """
    CREATE TABLE IF NOT EXISTS device_app_usage (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        application        VARCHAR(255) NOT NULL,
        category           VARCHAR(255),
        confidence         VARCHAR(20) NOT NULL DEFAULT 'LOW',
        hour_start         TIMESTAMPTZ NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        total_bytes        BIGINT,
        connections        BIGINT DEFAULT 0,
        evidence           JSONB
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_domain_usage (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        domain             VARCHAR(255) NOT NULL,
        category           VARCHAR(255),
        hour_start         TIMESTAMPTZ NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        total_bytes        BIGINT,
        queries            BIGINT DEFAULT 0,
        connections        BIGINT DEFAULT 0,
        confidence         VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
        evidence           JSONB
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_category_usage (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        category           VARCHAR(255) NOT NULL,
        hour_start         TIMESTAMPTZ NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        total_bytes        BIGINT,
        connections        BIGINT DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_protocol_usage (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        protocol           VARCHAR(255) NOT NULL,
        hour_start         TIMESTAMPTZ NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        total_bytes        BIGINT,
        packets            BIGINT DEFAULT 0,
        connections        BIGINT DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usage_hourly (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        hour_start         TIMESTAMPTZ NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        packets            BIGINT DEFAULT 0,
        connections        BIGINT DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usage_daily (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        day_start          DATE NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        packets            BIGINT DEFAULT 0,
        connections        BIGINT DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usage_monthly (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        month_start        DATE NOT NULL,
        download_bytes     BIGINT DEFAULT 0,
        upload_bytes       BIGINT DEFAULT 0,
        packets            BIGINT DEFAULT 0,
        connections        BIGINT DEFAULT 0
    )
    """,
    # --- Attribution supporting tables ---
    """
    CREATE TABLE IF NOT EXISTS dns_queries (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
        queried_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        domain             VARCHAR(255),
        query_type         VARCHAR(32),
        response_ip        INET
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sni_observations (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
        sni                VARCHAR(255) NOT NULL,
        destination_ip     INET,
        destination_port   INTEGER,
        observed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        bytes              BIGINT DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_peaks (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        peak_type          VARCHAR(255) NOT NULL,
        peak_value         BIGINT NOT NULL,
        peak_at            TIMESTAMPTZ NOT NULL,
        day                DATE NOT NULL,
        hour               INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_activity_timeline (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        hour_start         TIMESTAMPTZ NOT NULL,
        is_active          BOOLEAN DEFAULT FALSE,
        total_bytes        BIGINT DEFAULT 0,
        connections        BIGINT DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS speed_limits (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        download_limit_bps BIGINT,
        upload_limit_bps   BIGINT,
        enabled            BOOLEAN DEFAULT TRUE,
        created_at         TIMESTAMPTZ DEFAULT NOW(),
        updated_at         TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS data_limits (
        id                 BIGSERIAL PRIMARY KEY,
        device_id          VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
        daily_quota_bytes  BIGINT,
        weekly_quota_bytes BIGINT,
        monthly_quota_bytes BIGINT,
        used_bytes         BIGINT DEFAULT 0,
        reset_period       VARCHAR(20) DEFAULT 'DAILY',
        reset_day          INTEGER DEFAULT 1,
        action             VARCHAR(20) DEFAULT 'ALERT',
        enabled            BOOLEAN DEFAULT TRUE,
        created_at         TIMESTAMPTZ DEFAULT NOW(),
        updated_at         TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # --- Indexes (additive) ---
    "CREATE INDEX IF NOT EXISTS idx_flows_device_started ON flows (device_id, started_at)",
    "CREATE INDEX IF NOT EXISTS idx_traffic_samples_device_sampled ON traffic_samples (device_id, sampled_at)",
    "CREATE INDEX IF NOT EXISTS idx_device_app_usage_device_hour ON device_app_usage (device_id, hour_start)",
    "CREATE INDEX IF NOT EXISTS idx_device_domain_usage_device_hour ON device_domain_usage (device_id, hour_start)",
    "CREATE INDEX IF NOT EXISTS idx_dns_queries_response_ip ON dns_queries (response_ip)",
]

# Legacy columns that the old (stale) schema may have created under different
# names. These ALTER statements migrate any pre-existing partial table to the
# full shape without data loss.
COMPATIBILITY_ALTERS = [
    # traffic_samples: old schema used packet_count, errors as packets
    "ALTER TABLE traffic_samples ADD COLUMN IF NOT EXISTS packets BIGINT NOT NULL DEFAULT 0",
    "ALTER TABLE traffic_samples ADD COLUMN IF NOT EXISTS connections BIGINT NOT NULL DEFAULT 0",
    "ALTER TABLE traffic_samples ADD COLUMN IF NOT EXISTS download_speed_bps BIGINT NOT NULL DEFAULT 0",
    "ALTER TABLE traffic_samples ADD COLUMN IF NOT EXISTS upload_speed_bps BIGINT NOT NULL DEFAULT 0",
    # device_app_usage: add missing intelligence columns
    "ALTER TABLE device_app_usage ADD COLUMN IF NOT EXISTS category VARCHAR(255)",
    "ALTER TABLE device_app_usage ADD COLUMN IF NOT EXISTS total_bytes BIGINT",
    "ALTER TABLE device_app_usage ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    "ALTER TABLE device_app_usage ADD COLUMN IF NOT EXISTS evidence JSONB",
    # device_domain_usage
    "ALTER TABLE device_domain_usage ADD COLUMN IF NOT EXISTS category VARCHAR(255)",
    "ALTER TABLE device_domain_usage ADD COLUMN IF NOT EXISTS total_bytes BIGINT",
    "ALTER TABLE device_domain_usage ADD COLUMN IF NOT EXISTS queries BIGINT DEFAULT 0",
    "ALTER TABLE device_domain_usage ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    "ALTER TABLE device_domain_usage ADD COLUMN IF NOT EXISTS confidence VARCHAR(20) DEFAULT 'MEDIUM'",
    "ALTER TABLE device_domain_usage ADD COLUMN IF NOT EXISTS evidence JSONB",
    # device_category_usage
    "ALTER TABLE device_category_usage ADD COLUMN IF NOT EXISTS total_bytes BIGINT",
    "ALTER TABLE device_category_usage ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    # device_protocol_usage
    "ALTER TABLE device_protocol_usage ADD COLUMN IF NOT EXISTS total_bytes BIGINT",
    "ALTER TABLE device_protocol_usage ADD COLUMN IF NOT EXISTS packets BIGINT DEFAULT 0",
    "ALTER TABLE device_protocol_usage ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    # usage tables
    "ALTER TABLE usage_daily ADD COLUMN IF NOT EXISTS packets BIGINT DEFAULT 0",
    "ALTER TABLE usage_daily ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    "ALTER TABLE usage_hourly ADD COLUMN IF NOT EXISTS packets BIGINT DEFAULT 0",
    "ALTER TABLE usage_hourly ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    "ALTER TABLE usage_monthly ADD COLUMN IF NOT EXISTS packets BIGINT DEFAULT 0",
    "ALTER TABLE usage_monthly ADD COLUMN IF NOT EXISTS connections BIGINT DEFAULT 0",
    # dns_queries
    "ALTER TABLE dns_queries ADD COLUMN IF NOT EXISTS query_type VARCHAR(32)",
    # sni_observations
    "ALTER TABLE sni_observations ADD COLUMN IF NOT EXISTS destination_ip INET",
    "ALTER TABLE sni_observations ADD COLUMN IF NOT EXISTS destination_port INTEGER",
    "ALTER TABLE sni_observations ADD COLUMN IF NOT EXISTS bytes BIGINT DEFAULT 0",
    # network_rules: extended rule model (rule type, domain/pattern, schedule, priority)
    "ALTER TABLE network_rules ADD COLUMN IF NOT EXISTS rule_type VARCHAR(32) DEFAULT 'DOMAIN'",
    "ALTER TABLE network_rules ADD COLUMN IF NOT EXISTS domain VARCHAR(255)",
    "ALTER TABLE network_rules ADD COLUMN IF NOT EXISTS schedule VARCHAR(255)",
    "ALTER TABLE network_rules ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0",
    "ALTER TABLE network_rules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
]


def initialize_database():
    """Create/ensure the full database schema (idempotent).

    Runs each migration in a dedicated transaction so a failure in one
    statement does not abort the others. Then applies additive compatibility
    ALTERs to migrate any legacy/partial tables to the full schema.

    This is the SINGLE SOURCE OF TRUTH for schema, kept in sync with the
    real production database (schema_out.txt).
    """
    from database.connection import get_connection, return_connection

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for migration in MIGRATIONS:
                try:
                    cursor.execute(migration)
                except Exception as exc:
                    logger.warning(
                        "Migration skipped: %s (%s)",
                        migration.strip().splitlines()[0][:80],
                        exc,
                    )
            for alter in COMPATIBILITY_ALTERS:
                try:
                    cursor.execute(alter)
                except Exception as exc:
                    logger.warning(
                        "Compatibility alter skipped: %s (%s)",
                        alter.strip().splitlines()[0][:80],
                        exc,
                    )
        conn.commit()
        logger.info(
            "Database schema initialization complete "
            "(%d migrations, %d alters)",
            len(MIGRATIONS),
            len(COMPATIBILITY_ALTERS),
        )
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        conn.rollback()
        raise
    finally:
        return_connection(conn)