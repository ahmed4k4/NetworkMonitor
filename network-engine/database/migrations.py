from database.connection import get_connection
from logger import logger


SCHEMA = """

-- ============================================
-- CORE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(64) PRIMARY KEY,
    mac_address MACADDR UNIQUE NOT NULL,
    ip_address INET,
    hostname VARCHAR(255),
    vendor VARCHAR(255),
    interface_name VARCHAR(100),
    state VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_upload BIGINT NOT NULL DEFAULT 0,
    total_download BIGINT NOT NULL DEFAULT 0,
    total_packets BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);
CREATE INDEX IF NOT EXISTS idx_devices_state ON devices(state);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);


CREATE TABLE IF NOT EXISTS interfaces (
    name VARCHAR(100) PRIMARY KEY,
    description TEXT,
    mac_address MACADDR,
    ip_address INET,
    network CIDR,
    speed_mbps NUMERIC,
    status VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================
-- FLOW & TRAFFIC TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS flows (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    source_ip INET NOT NULL,
    destination_ip INET NOT NULL,
    source_port INTEGER,
    destination_port INTEGER,
    protocol VARCHAR(32),
    interface_name VARCHAR(100),
    direction VARCHAR(20),
    started_at TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    duration_seconds BIGINT DEFAULT 0,
    packets BIGINT DEFAULT 0,
    bytes BIGINT DEFAULT 0,
    upload_bytes BIGINT DEFAULT 0,
    download_bytes BIGINT DEFAULT 0,
    state VARCHAR(20) DEFAULT 'ACTIVE'
);

CREATE INDEX IF NOT EXISTS idx_flows_device_id ON flows(device_id);
CREATE INDEX IF NOT EXISTS idx_flows_start_time ON flows(started_at);
CREATE INDEX IF NOT EXISTS idx_flows_state ON flows(state);


CREATE TABLE IF NOT EXISTS traffic_samples (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    sampled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    download_bytes BIGINT NOT NULL DEFAULT 0,
    upload_bytes BIGINT NOT NULL DEFAULT 0,
    packets BIGINT NOT NULL DEFAULT 0,
    connections BIGINT NOT NULL DEFAULT 0,
    download_speed_bps BIGINT NOT NULL DEFAULT 0,
    upload_speed_bps BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_traffic_samples_device_id ON traffic_samples(device_id);
CREATE INDEX IF NOT EXISTS idx_traffic_samples_timestamp ON traffic_samples(sampled_at);


CREATE TABLE IF NOT EXISTS connections (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    source_ip INET,
    destination_ip INET,
    source_port INTEGER,
    destination_port INTEGER,
    protocol VARCHAR(32),
    started_at TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    state VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_connections_device_id ON connections(device_id);
CREATE INDEX IF NOT EXISTS idx_connections_state ON connections(state);
CREATE INDEX IF NOT EXISTS idx_connections_last_seen ON connections(last_seen);


-- ============================================
-- DNS & APPLICATION TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS dns_queries (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
    queried_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    domain VARCHAR(255),
    query_type VARCHAR(32),
    response_ip INET
);

CREATE INDEX IF NOT EXISTS idx_dns_queries_device_id ON dns_queries(device_id);
CREATE INDEX IF NOT EXISTS idx_dns_queries_domain ON dns_queries(domain);


CREATE TABLE IF NOT EXISTS domains (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS applications (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS protocols (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    packets BIGINT DEFAULT 0,
    bytes BIGINT DEFAULT 0
);


-- ============================================
-- USAGE ANALYTICS TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS usage_hourly (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    hour_start TIMESTAMPTZ NOT NULL,
    download_bytes BIGINT DEFAULT 0,
    upload_bytes BIGINT DEFAULT 0,
    packets BIGINT DEFAULT 0,
    connections BIGINT DEFAULT 0,
    UNIQUE(device_id, hour_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_hourly_device_id ON usage_hourly(device_id);


CREATE TABLE IF NOT EXISTS usage_daily (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    day_start DATE NOT NULL,
    download_bytes BIGINT DEFAULT 0,
    upload_bytes BIGINT DEFAULT 0,
    packets BIGINT DEFAULT 0,
    connections BIGINT DEFAULT 0,
    UNIQUE(device_id, day_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_daily_device_id ON usage_daily(device_id);


CREATE TABLE IF NOT EXISTS usage_monthly (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    month_start DATE NOT NULL,
    download_bytes BIGINT DEFAULT 0,
    upload_bytes BIGINT DEFAULT 0,
    packets BIGINT DEFAULT 0,
    connections BIGINT DEFAULT 0,
    UNIQUE(device_id, month_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_monthly_device_id ON usage_monthly(device_id);


-- ============================================
-- CONTROL TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS speed_limits (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    download_limit_bps BIGINT,
    upload_limit_bps BIGINT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(device_id)
);


CREATE TABLE IF NOT EXISTS data_limits (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    daily_quota_bytes BIGINT,
    weekly_quota_bytes BIGINT,
    monthly_quota_bytes BIGINT,
    used_bytes BIGINT DEFAULT 0,
    reset_period VARCHAR(20),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(device_id)
);


CREATE TABLE IF NOT EXISTS firewall_rules (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
    direction VARCHAR(20),
    protocol VARCHAR(32),
    source_ip INET,
    destination_ip INET,
    source_port INTEGER,
    destination_port INTEGER,
    action VARCHAR(20),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================
-- MONITORING TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
    alert_type VARCHAR(100),
    severity VARCHAR(20),
    message TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);


CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
    event_type VARCHAR(100),
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_device_id ON events(device_id);


CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    user_id VARCHAR(255),
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_device_id ON audit_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);


-- ============================================
-- REPORTING & CONFIGURATION
-- ============================================

CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

"""

# ============================================================
# MIGRATIONS for existing databases
# ============================================================

MIGRATIONS = [
    """
    ALTER TABLE data_limits
        ADD COLUMN IF NOT EXISTS daily_quota_bytes BIGINT,
        ADD COLUMN IF NOT EXISTS weekly_quota_bytes BIGINT,
        ADD COLUMN IF NOT EXISTS monthly_quota_bytes BIGINT,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
    """,
    """
    ALTER TABLE data_limits
        ADD COLUMN IF NOT EXISTS quota_bytes2 BIGINT
    """,
    """
    UPDATE data_limits
    SET daily_quota_bytes = quota_bytes
    WHERE daily_quota_bytes IS NULL AND quota_bytes IS NOT NULL
    """,
    """
    ALTER TABLE speed_limits
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
    """,
    """
    ALTER TABLE traffic_samples
        ADD COLUMN IF NOT EXISTS download_speed_bps BIGINT NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS upload_speed_bps BIGINT NOT NULL DEFAULT 0
    """,
]


def initialize_database():
    """Initialize database with schema and apply migrations"""

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(SCHEMA)

            # Apply migrations for existing databases
            for migration in MIGRATIONS:
                try:
                    cursor.execute(migration)
                    logger.info("Migration applied successfully")
                except Exception as migration_error:
                    logger.warning(f"Migration skipped: {migration_error}")

        connection.commit()
        logger.info("Database schema initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        connection.rollback()
        raise

    finally:

        connection.close()
