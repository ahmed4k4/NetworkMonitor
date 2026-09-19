# Network Control Database Documentation

## Overview

This document describes the database architecture, buffering strategy, retention policies, and recovery mechanisms for the Network Control platform.

## Database Architecture

### Core Tables

| Table | Purpose | Retention |
|-------|---------|-----------|
| `devices` | Device registry with MAC-based identity | Permanent |
| `flows` | Raw packet-level flow records | 7 days |
| `traffic_samples` | Per-second bandwidth samples | 30 days |
| `connections` | Active TCP/UDP connection tracking | 30 days |

### Intelligence Tables (Hourly Aggregates)

| Table | Purpose | Retention |
|-------|---------|-----------|
| `device_app_usage` | Application attribution with confidence | 90 days |
| `device_domain_usage` | Domain-level usage with evidence | 90 days |
| `device_category_usage` | Category breakdown (Streaming, Gaming, etc.) | 90 days |
| `device_protocol_usage` | Protocol breakdown (HTTPS, QUIC, DNS, etc.) | 90 days |
| `usage_hourly` | Total traffic per device per hour | 90 days |
| `device_peaks` | Peak speed/connections per device per hour | 365 days |
| `device_activity_timeline` | Hourly active/inactive status | 365 days |

### Long-term Aggregates

| Table | Purpose | Retention |
|-------|---------|-----------|
| `usage_daily` | Daily traffic totals per device | 2 years |
| `usage_monthly` | Monthly traffic totals per device | 5 years |

### Supporting Tables

| Table | Purpose | Retention |
|-------|---------|-----------|
| `dns_queries` | DNS queries for attribution | 30 days |
| `sni_observations` | TLS SNI observations | 30 days |
| `audit_logs` | Admin action audit trail | 1 year |
| `alerts` | Generated alerts | 1 year |
| `events` | System events | 30 days |

### Control Tables

| Table | Purpose |
|-------|---------|
| `speed_limits` | Per-device bandwidth limits |
| `data_limits` | Per-device data quotas |
| `firewall_rules` | Blocking/allow rules |
| `network_rules` | Traffic shaping rules |
| `settings` | System configuration |

## Buffering Strategy

### In-Memory Buffering (Real-time)

The system uses multi-layer buffering to handle high-frequency packet processing:

1. **Packet-Level Buffering** (FlowManager)
   - Active flows held in memory: `self.flows` dictionary
   - Key: normalized endpoint pair + protocol
   - Timeout: 60 seconds (configurable)
   - Cleanup: periodic every 60 seconds

2. **Per-Device Byte Counters** (NetworkEngine)
   - `self.device_bytes[device_id]` - cumulative counters
   - `self.last_sample_bytes[device_id]` - previous sample baseline
   - Delta computed every 10 seconds for traffic samples

3. **Bandwidth Tracker** (BandwidthTracker)
   - Rolling time-window counters (10-second window default)
   - Per-device and global speed calculations
   - Peak detection

4. **Connection Tracker** (ConnectionTracker)
   - Active TCP/UDP connections in memory
   - State machine for connection lifecycle

### Database Write Buffering

**Traffic Samples** (every 10 seconds):
- Real byte deltas computed from in-memory counters
- Written via `TrafficRepository.save_delta_sample()`
- Single connection per batch, committed immediately

**Flow Persistence** (on flow close):
- Flows closed by timeout → `_attribute_and_save_flow()`
- Attribution performed inline
- Intelligence tables updated with `ON CONFLICT ... DO UPDATE`
- Each flow commit is a separate transaction

**Device Discovery** (every 10 seconds):
- ARP scan results upserted to `devices` table
- Offline detection via comparison with previous scan

### Transaction Strategy

| Operation | Transaction Scope | Rollback Behavior |
|-----------|-------------------|-------------------|
| Device upsert | Single row | Full rollback on error |
| Flow save | Single flow | Log error, continue |
| Traffic sample | Batch of devices | Full rollback on error |
| Attribution save | Per-intelligence-table | Rollback per table |
| Quota update | Single quota record | Rollback on error |

**Connection Pooling:**
- Uses `psycopg_pool.ConnectionPool` (min=2, max=10)
- Connections acquired via `get_pool().connection()`
- Automatic return via context manager
- Pool closed on engine shutdown

## Retention Policies

### Automated Cleanup

Retention cleanup runs daily (every 8640 cycles at 10s interval = 24 hours).

```python
from database.retention import cleanup_old_data, get_table_sizes
cleanup_old_data()  # Deletes old data in batches of 10,000 rows
get_table_sizes()   # Logs current table sizes for monitoring
```

### Retention Configuration

```python
RETENTION_POLICIES = {
    "flows": 7,
    "traffic_samples": 30,
    "dns_queries": 30,
    "sni_observations": 30,
    "connections": 30,
    "events": 30,
    "device_app_usage": 90,
    "device_domain_usage": 90,
    "device_category_usage": 90,
    "device_protocol_usage": 90,
    "usage_hourly": 90,
    "device_peaks": 365,
    "device_activity_timeline": 365,
    "usage_daily": 730,
    "usage_monthly": 1825,
    "audit_logs": 365,
    "alerts": 365,
}
```

### Batch Deletion

To avoid long table locks:
- Deletes in batches of 10,000 rows
- Uses `ctid` for efficient row selection
- Commits between batches
- 100ms pause between batches

## Recovery Mechanisms

### Engine Restart Recovery

1. **Device Identity Preservation**
   - MAC-based identity survives DHCP/IP changes
   - `DeviceIdentityManager` maps MAC → stable `device_id`
   - Historical data linked by `device_id`, not IP

2. **Cumulative Counters**
   - `devices.total_upload/download` never reset
   - Usage deltas computed from last sample baseline
   - Restart: baseline starts from current in-memory state
   - Historical `usage_daily` preserved

3. **Flow Recovery**
   - In-memory flows lost on restart (expected)
   - Only closed flows persisted to database
   - Active flows at restart time: not saved (acceptable loss < 60s data)

4. **Quota State**
   - `data_limits.used_bytes` persists in database
   - QuotaEngine reloads state on initialization
   - `check_and_reset_quotas()` runs periodically

### Database Failure Handling

**Connection Failures:**
- Connection pool handles reconnection
- `get_connection()` retries via pool
- Repository methods catch exceptions, log, rollback, re-raise

**Transaction Failures:**
- Each repository method wraps in try/except
- `connection.rollback()` on error
- Critical path errors propagate to caller
- Non-critical errors (attribution) logged, flow processing continues

**Disk Full / Corruption:**
- PostgreSQL WAL protects against corruption
- Regular `VACUUM ANALYZE` via `retention.vacuum_analyze()`
- Monitoring: `get_table_sizes()` logs growth trends

### Backup Strategy

```powershell
# PowerShell backup script (BACKUP.ps1)
pg_dump -h 127.0.0.1 -U network_admin -d network_control > backup_$(date).sql
```

**Recommended schedule:**
- Daily: Full dump (compressed)
- Weekly: Verify restore test
- Retention: 30 daily, 12 weekly, 12 monthly

### Point-in-Time Recovery

PostgreSQL WAL enables PITR:
```sql
-- Enable WAL archiving in postgresql.conf
archive_mode = on
archive_command = 'copy "%p" "C:/backups/wal/%f"'
```

## Performance Optimizations

### Indexes

Key indexes for query performance:
- `flows`: `(device_id, started_at)`, `(state)`, unique constraint on 7 columns
- `traffic_samples`: `(device_id, sampled_at)`
- `device_app_usage`: `(device_id, hour_start)`, `(application)`, `(confidence)`
- `device_domain_usage`: `(device_id, hour_start)`, `(domain)`
- `usage_daily`: `(device_id, day_start)` unique
- `audit_logs`: `(device_id, created_at)`, `(event_type)`

### Query Patterns to Avoid

1. **N+1 Queries**: API routes batch intelligence queries
2. **Full Table Scans**: All queries filtered by `device_id` + time range
3. **Missing Indexes**: All foreign keys indexed; time-series columns indexed

### Monitoring

```python
# Check table sizes
from database.retention import get_table_sizes
get_table_sizes()

# Check query performance (if pg_stat_statements enabled)
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY total_exec_time DESC LIMIT 20;
```

## API Endpoints for Database Health

- `GET /api/system/health` - Overall system health
- `GET /api/system/database/stats` - Table sizes, connection count
- `POST /api/admin/database/cleanup` - Manual retention cleanup
- `POST /api/admin/database/vacuum` - Manual VACUUM ANALYZE

## Data Integrity Rules

1. **Unique Constraints**:
   - `devices.mac_address` - one device per MAC
   - `flows` 7-column unique - prevents duplicate flow records
   - Intelligence tables: `(device_id, entity, hour_start)` unique

2. **Foreign Keys**:
   - All device_id columns REFERENCES devices(device_id) ON DELETE CASCADE
   - Cascade ensures cleanup when device removed

3. **Generated Columns**:
   - `device_app_usage.total_bytes` = download + upload (STORED)
   - `device_domain_usage.total_bytes` = download + upload (STORED)
   - `device_category_usage.total_bytes` = download + upload (STORED)
   - `device_protocol_usage.total_bytes` = download + upload (STORED)

4. **Confidence Levels**:
   - Application attribution: HIGH / MEDIUM / LOW
   - Stored as VARCHAR(20) with CHECK constraint recommended
   - Displayed in UI with visual indicators

## Migration Safety

- Migrations in `MIGRATIONS` list are additive only
- `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` patterns
- No DROP COLUMN or DROP TABLE in migrations
- Schema changes deployed via `initialize_database()`

## Future Improvements

1. **TimescaleDB**: Consider hypertable for `flows`, `traffic_samples`
2. **Partitioning**: Native partitioning for hourly/daily tables
3. **pg_stat_statements**: Enable in postgresql.conf for query analysis
4. **Read Replicas**: For dashboard query scaling
5. **Compression**: TOAST compression for JSONB evidence columns