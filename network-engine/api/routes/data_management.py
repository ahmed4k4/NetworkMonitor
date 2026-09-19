"""
Data Management API Routes

Provides comprehensive data management capabilities:
- Database statistics and table information
- Data export (CSV, Excel, PDF)
- Controlled data deletion with confirmation
- Backup and restore operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import csv
import io
import os
import tempfile
import json
import subprocess
import shutil

from database.connection import get_connection, return_connection
from api.security import get_current_user, require_permission
from database.audit import log_admin_action

router = APIRouter(tags=["Data Management"])


# ============================================================
# MODELS
# ============================================================

class ExportRequest(BaseModel):
    """Data export request with filtering options"""
    format: str = Field(default="csv", pattern="^(csv|excel|pdf)$")
    data_type: str = Field(..., pattern="^(flows|traffic_samples|dns_queries|domains|applications|usage_daily|usage_hourly|usage_monthly|alerts|events|audit_logs|device_app_usage|device_domain_usage|device_category_usage|device_protocol_usage|device_peaks|device_activity_timeline|sni_observations)$")
    device_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    traffic_type: Optional[str] = None  # download, upload, both
    domain: Optional[str] = None
    application: Optional[str] = None
    limit: int = Field(default=10000, le=100000)


class DeleteRequest(BaseModel):
    """Data deletion request with confirmation"""
    data_type: str = Field(..., pattern="^(flows|traffic_samples|dns_queries|domains|applications|usage_daily|usage_hourly|usage_monthly|alerts|events|audit_logs|device_app_usage|device_domain_usage|device_category_usage|device_protocol_usage|device_peaks|device_activity_timeline|sni_observations|all)$")
    device_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    confirm: bool = Field(default=False, description="Must be true to confirm deletion")
    reason: str = Field(default="", description="Reason for deletion (required for audit)")


class BackupRequest(BaseModel):
    """Backup request"""
    backup_type: str = Field(default="full", pattern="^(full|config|database|rules)$")
    include_data: bool = True
    description: Optional[str] = None


class RestoreRequest(BaseModel):
    """Restore request"""
    backup_id: str = Field(..., description="Backup identifier/directory name")
    confirm: bool = Field(default=False, description="Must be true to confirm restore")
    restore_data: bool = True


# ============================================================
# DATABASE STATISTICS
# ============================================================

@router.get("/stats")
def get_database_stats(user=Depends(require_permission("reports:read"))):
    """
    Get comprehensive database statistics:
    - Database size
    - Table sizes and row counts
    - Record counts for each data category
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get table sizes
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
            table_sizes = cursor.fetchall()
            
            # Get database total size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]
            
            # Get record counts for key tables
            key_tables = {
                "devices": "devices",
                "flows": "flows",
                "traffic_samples": "traffic_samples",
                "dns_queries": "dns_queries",
                "domains": "domains",
                "applications": "applications",
                "usage_daily": "usage_daily",
                "usage_hourly": "usage_hourly",
                "usage_monthly": "usage_monthly",
                "alerts": "alerts",
                "events": "events",
                "audit_logs": "audit_logs",
                "device_app_usage": "device_app_usage",
                "device_domain_usage": "device_domain_usage",
                "device_category_usage": "device_category_usage",
                "device_protocol_usage": "device_protocol_usage",
                "device_peaks": "device_peaks",
                "device_activity_timeline": "device_activity_timeline",
                "sni_observations": "sni_observations",
                "speed_limits": "speed_limits",
                "data_limits": "data_limits",
                "network_rules": "network_rules",
                "firewall_rules": "firewall_rules",
                "connections": "connections",
                "interfaces": "interfaces",
                "settings": "settings",
            }
            
            record_counts = {}
            for key, table in key_tables.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    record_counts[key] = cursor.fetchone()[0]
                except Exception:
                    record_counts[key] = 0
            
            # Build table info
            tables = []
            for row in table_sizes:
                tables.append({
                    "name": row[1],
                    "size": row[2],
                    "size_bytes": row[3],
                    "estimated_rows": row[4],
                    "record_count": record_counts.get(row[1], 0)
                })
            
            # Calculate totals
            total_rows = sum(record_counts.values())
            
            return {
                "database_size": db_size,
                "total_tables": len(tables),
                "total_rows": total_rows,
                "tables": tables,
                "record_counts": record_counts,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {error}")
    finally:
        return_connection(connection)


@router.get("/tables")
def list_tables(user=Depends(require_permission("reports:read"))):
    """List all database tables with metadata"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            rows = cursor.fetchall()
            
        return [
            {"name": row[0], "column_count": row[1]}
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {error}")
    finally:
        return_connection(connection)


# ============================================================
# DATA EXPORT
# ============================================================

def build_export_query(data_type: str, filters: dict) -> tuple:
    """Build SQL query and parameters for export based on data type and filters"""
    
    # Define table schemas and default columns
    table_configs = {
        "flows": {
            "table": "flows",
            "columns": "id, device_id, source_ip, destination_ip, source_port, destination_port, protocol, interface_name, direction, started_at, last_seen, duration_seconds, packets, bytes, upload_bytes, download_bytes, state",
            "time_column": "started_at",
            "device_column": "device_id"
        },
        "traffic_samples": {
            "table": "traffic_samples",
            "columns": "id, device_id, sampled_at, download_bytes, upload_bytes, packets, connections, download_speed_bps, upload_speed_bps",
            "time_column": "sampled_at",
            "device_column": "device_id"
        },
        "dns_queries": {
            "table": "dns_queries",
            "columns": "id, device_id, queried_at, domain, query_type, response_ip",
            "time_column": "queried_at",
            "device_column": "device_id"
        },
        "domains": {
            "table": "domains",
            "columns": "id, domain, category, first_seen, last_seen",
            "time_column": "first_seen",
            "device_column": None
        },
        "applications": {
            "table": "applications",
            "columns": "id, name, category, first_seen, last_seen",
            "time_column": "first_seen",
            "device_column": None
        },
        "usage_daily": {
            "table": "usage_daily",
            "columns": "id, device_id, day_start, download_bytes, upload_bytes, packets, connections",
            "time_column": "day_start",
            "device_column": "device_id"
        },
        "usage_hourly": {
            "table": "usage_hourly",
            "columns": "id, device_id, hour_start, download_bytes, upload_bytes, packets, connections",
            "time_column": "hour_start",
            "device_column": "device_id"
        },
        "usage_monthly": {
            "table": "usage_monthly",
            "columns": "id, device_id, month_start, download_bytes, upload_bytes, packets, connections",
            "time_column": "month_start",
            "device_column": "device_id"
        },
        "alerts": {
            "table": "alerts",
            "columns": "id, device_id, alert_type, severity, message, resolved, created_at, resolved_at",
            "time_column": "created_at",
            "device_column": "device_id"
        },
        "events": {
            "table": "events",
            "columns": "id, device_id, event_type, message, created_at",
            "time_column": "created_at",
            "device_column": "device_id"
        },
        "audit_logs": {
            "table": "audit_logs",
            "columns": "id, event_type, message, user_id, device_id, metadata, created_at",
            "time_column": "created_at",
            "device_column": "device_id"
        },
        "device_app_usage": {
            "table": "device_app_usage",
            "columns": "id, device_id, application, category, confidence, hour_start, download_bytes, upload_bytes, total_bytes, connections, evidence",
            "time_column": "hour_start",
            "device_column": "device_id"
        },
        "device_domain_usage": {
            "table": "device_domain_usage",
            "columns": "id, device_id, domain, category, hour_start, download_bytes, upload_bytes, total_bytes, queries, connections",
            "time_column": "hour_start",
            "device_column": "device_id"
        },
        "device_category_usage": {
            "table": "device_category_usage",
            "columns": "id, device_id, category, hour_start, download_bytes, upload_bytes, total_bytes, connections",
            "time_column": "hour_start",
            "device_column": "device_id"
        },
        "device_protocol_usage": {
            "table": "device_protocol_usage",
            "columns": "id, device_id, protocol, hour_start, download_bytes, upload_bytes, total_bytes, packets, connections",
            "time_column": "hour_start",
            "device_column": "device_id"
        },
        "device_peaks": {
            "table": "device_peaks",
            "columns": "id, device_id, peak_type, peak_value, peak_at, day, hour",
            "time_column": "peak_at",
            "device_column": "device_id"
        },
        "device_activity_timeline": {
            "table": "device_activity_timeline",
            "columns": "id, device_id, hour_start, is_active, total_bytes, connections",
            "time_column": "hour_start",
            "device_column": "device_id"
        },
        "sni_observations": {
            "table": "sni_observations",
            "columns": "id, device_id, sni, destination_ip, destination_port, observed_at, bytes",
            "time_column": "observed_at",
            "device_column": "device_id"
        },
    }
    
    if data_type not in table_configs:
        raise ValueError(f"Unsupported data type: {data_type}")
    
    config = table_configs[data_type]
    table = config["table"]
    columns = config["columns"]
    time_column = config["time_column"]
    device_column = config["device_column"]
    
    where_clauses = []
    params = []
    
    # Device filter
    if filters.get("device_id") and device_column:
        where_clauses.append(f"{device_column} = %s")
        params.append(filters["device_id"])
    
    # Date range filter
    if filters.get("start_date"):
        where_clauses.append(f"{time_column} >= %s")
        params.append(filters["start_date"])
    
    if filters.get("end_date"):
        where_clauses.append(f"{time_column} <= %s")
        params.append(filters["end_date"] + timedelta(days=1))  # Include end date
    
    # Domain filter
    if filters.get("domain") and data_type in ("dns_queries", "domains", "device_domain_usage"):
        col = "domain" if data_type != "dns_queries" else "domain"
        where_clauses.append(f"{col} ILIKE %s")
        params.append(f"%{filters['domain']}%")
    
    # Application filter
    if filters.get("application") and data_type in ("device_app_usage", "applications"):
        col = "application" if data_type != "applications" else "name"
        where_clauses.append(f"{col} ILIKE %s")
        params.append(f"%{filters['application']}%")
    
    # Traffic type filter (for traffic_samples)
    if filters.get("traffic_type") and data_type == "traffic_samples":
        if filters["traffic_type"] == "download":
            where_clauses.append("download_bytes > 0")
        elif filters["traffic_type"] == "upload":
            where_clauses.append("upload_bytes > 0")
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    limit = filters.get("limit", 10000)
    
    query = f"""
        SELECT {columns}
        FROM {table}
        {where_sql}
        ORDER BY {time_column} DESC
        LIMIT %s
    """
    params.append(limit)
    
    return query, params


def stream_csv(query: str, params: list) -> StreamingResponse:
    """Stream query results as CSV"""
    connection = get_connection()
    
    def generate():
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                
                # Write header
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(columns)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                
                # Write data rows
                while True:
                    rows = cursor.fetchmany(1000)
                    if not rows:
                        break
                    writer.writerows(rows)
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
        finally:
            return_connection(connection)
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


def stream_excel(query: str, params: list, data_type: str) -> StreamingResponse:
    """Stream query results as Excel (xlsx)"""
    connection = get_connection()
    
    def generate():
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Create Excel in memory
                from openpyxl import Workbook
                from openpyxl.styles import Font
                
                wb = Workbook()
                ws = wb.active
                ws.title = data_type[:31]  # Excel sheet name limit
                
                # Header
                header_font = Font(bold=True)
                for col_idx, col_name in enumerate(columns, 1):
                    cell = ws.cell(row=1, column=col_idx, value=col_name)
                    cell.font = header_font
                
                # Data
                for row_idx, row in enumerate(rows, 2):
                    for col_idx, value in enumerate(row, 1):
                        ws.cell(row=row_idx, column=col_idx, value=value)
                
                # Save to bytes
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                yield output.read()
        finally:
            return_connection(connection)
    
    return StreamingResponse(
        generate(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=export_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
    )


def generate_pdf(query: str, params: list, data_type: str) -> FileResponse:
    """Generate PDF report from query results"""
    connection = get_connection()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
    finally:
        return_connection(connection)
    
    # Create HTML for PDF generation
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 9px; }}
            th, td {{ border: 1px solid #ddd; padding: 4px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .meta {{ color: #666; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>{data_type.replace('_', ' ').title()} Report</h1>
        <div class="meta">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            Records: {len(rows)}<br>
            Filters: {json.dumps(params[:-1] if params else {}, default=str)}
        </div>
        <table>
            <thead><tr>{''.join(f'<th>{c}</th>' for c in columns)}</tr></thead>
            <tbody>
    """
    
    for row in rows[:5000]:  # Limit PDF to 5000 rows
        html += "<tr>" + "".join(f"<td>{v if v is not None else ''}</td>" for v in row) + "</tr>"
    
    html += """
            </tbody>
        </table>
        <div class="meta">Showing first 5000 rows. Use CSV/Excel for full export.</div>
    </body>
    </html>
    """
    
    # Write HTML to temp file and convert to PDF
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        html_path = f.name
    
    pdf_path = html_path.replace('.html', '.pdf')
    
    try:
        # Try using wkhtmltopdf if available, otherwise use weasyprint
        try:
            subprocess.run(['wkhtmltopdf', html_path, pdf_path], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: use weasyprint if available
            try:
                from weasyprint import HTML
                HTML(html_path).write_pdf(pdf_path)
            except ImportError:
                # Last resort: return HTML file
                os.unlink(html_path)
                raise HTTPException(status_code=501, detail="PDF generation requires wkhtmltopdf or weasyprint. Install one of them.")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"export_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            background=lambda: (os.unlink(html_path), os.unlink(pdf_path))
        )
    except Exception as e:
        if os.path.exists(html_path):
            os.unlink(html_path)
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/export")
def export_data(request: ExportRequest, user=Depends(require_permission("reports:read"))):
    """
    Export data in CSV, Excel, or PDF format with filtering options.
    Uses real database data only - no generated/mock data.
    """
    try:
        query, params = build_export_query(request.data_type, {
            "device_id": request.device_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "traffic_type": request.traffic_type,
            "domain": request.domain,
            "application": request.application,
            "limit": request.limit,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Log export action
    log_admin_action(
        user["username"], 
        "EXPORT", 
        f"data:{request.data_type}", 
        "none", 
        f"format={request.format}, device={request.device_id}, date_range={request.start_date} to {request.end_date}"
    )
    
    if request.format == "csv":
        return stream_csv(query, params)
    elif request.format == "excel":
        return stream_excel(query, params, request.data_type)
    elif request.format == "pdf":
        return generate_pdf(query, params, request.data_type)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


# ============================================================
# DATA DELETION
# ============================================================

def build_delete_query(data_type: str, filters: dict) -> tuple:
    """Build DELETE query and parameters based on data type and filters"""
    
    table_configs = {
        "flows": {"table": "flows", "time_column": "started_at", "device_column": "device_id"},
        "traffic_samples": {"table": "traffic_samples", "time_column": "sampled_at", "device_column": "device_id"},
        "dns_queries": {"table": "dns_queries", "time_column": "queried_at", "device_column": "device_id"},
        "domains": {"table": "domains", "time_column": "first_seen", "device_column": None},
        "applications": {"table": "applications", "time_column": "first_seen", "device_column": None},
        "usage_daily": {"table": "usage_daily", "time_column": "day_start", "device_column": "device_id"},
        "usage_hourly": {"table": "usage_hourly", "time_column": "hour_start", "device_column": "device_id"},
        "usage_monthly": {"table": "usage_monthly", "time_column": "month_start", "device_column": "device_id"},
        "alerts": {"table": "alerts", "time_column": "created_at", "device_column": "device_id"},
        "events": {"table": "events", "time_column": "created_at", "device_column": "device_id"},
        "audit_logs": {"table": "audit_logs", "time_column": "created_at", "device_column": "device_id"},
        "device_app_usage": {"table": "device_app_usage", "time_column": "hour_start", "device_column": "device_id"},
        "device_domain_usage": {"table": "device_domain_usage", "time_column": "hour_start", "device_column": "device_id"},
        "device_category_usage": {"table": "device_category_usage", "time_column": "hour_start", "device_column": "device_id"},
        "device_protocol_usage": {"table": "device_protocol_usage", "time_column": "hour_start", "device_column": "device_id"},
        "device_peaks": {"table": "device_peaks", "time_column": "peak_at", "device_column": "device_id"},
        "device_activity_timeline": {"table": "device_activity_timeline", "time_column": "hour_start", "device_column": "device_id"},
        "sni_observations": {"table": "sni_observations", "time_column": "observed_at", "device_column": "device_id"},
    }
    
    if data_type == "all":
        return "ALL_TABLES", None
    
    if data_type not in table_configs:
        raise ValueError(f"Unsupported data type: {data_type}")
    
    config = table_configs[data_type]
    table = config["table"]
    time_column = config["time_column"]
    device_column = config["device_column"]
    
    where_clauses = []
    params = []
    
    if filters.get("device_id") and device_column:
        where_clauses.append(f"{device_column} = %s")
        params.append(filters["device_id"])
    
    if filters.get("start_date"):
        where_clauses.append(f"{time_column} >= %s")
        params.append(filters["start_date"])
    
    if filters.get("end_date"):
        where_clauses.append(f"{time_column} <= %s")
        params.append(filters["end_date"] + timedelta(days=1))
    
    if not where_clauses:
        raise ValueError("At least one filter (device_id, start_date, or end_date) is required for deletion")
    
    where_sql = "WHERE " + " AND ".join(where_clauses)
    query = f"DELETE FROM {table} {where_sql}"
    
    return query, params


@router.post("/delete")
def delete_data(request: DeleteRequest, user=Depends(require_permission("system_operations"))):
    """
    Delete data with confirmation and audit logging.
    Requires explicit confirmation and appropriate permissions.
    """
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Deletion requires explicit confirmation (confirm=true)")
    
    if not request.reason:
        raise HTTPException(status_code=400, detail="Reason is required for audit trail")
    
    connection = get_connection()
    
    try:
        with connection.cursor() as cursor:
            if request.data_type == "all":
                # Get all tables with retention policies
                tables = [
                    "flows", "traffic_samples", "dns_queries", "domains", "applications",
                    "usage_daily", "usage_hourly", "usage_monthly",
                    "alerts", "events", "audit_logs",
                    "device_app_usage", "device_domain_usage", "device_category_usage",
                    "device_protocol_usage", "device_peaks", "device_activity_timeline",
                    "sni_observations"
                ]
                
                # Only delete tables that exist and match filters
                total_deleted = 0
                deleted_details = {}
                
                for table in tables:
                    # Check if table exists
                    cursor.execute("""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = %s
                    """, (table,))
                    
                    if cursor.fetchone():
                        # Build WHERE clause for this table
                        time_columns = {
                            "flows": "started_at", "traffic_samples": "sampled_at",
                            "dns_queries": "queried_at", "domains": "first_seen",
                            "applications": "first_seen", "usage_daily": "day_start",
                            "usage_hourly": "hour_start", "usage_monthly": "month_start",
                            "alerts": "created_at", "events": "created_at",
                            "audit_logs": "created_at",
                            "device_app_usage": "hour_start", "device_domain_usage": "hour_start",
                            "device_category_usage": "hour_start", "device_protocol_usage": "hour_start",
                            "device_peaks": "peak_at", "device_activity_timeline": "hour_start",
                            "sni_observations": "observed_at",
                        }
                        
                        time_col = time_columns.get(table)
                        if not time_col:
                            continue
                        
                        device_col = "device_id" if table != "domains" and table != "applications" else None
                        
                        where_clauses = []
                        params = []
                        
                        if request.device_id and device_col:
                            where_clauses.append(f"{device_col} = %s")
                            params.append(request.device_id)
                        
                        if request.start_date:
                            where_clauses.append(f"{time_col} >= %s")
                            params.append(request.start_date)
                        
                        if request.end_date:
                            where_clauses.append(f"{time_col} <= %s")
                            params.append(request.end_date + timedelta(days=1))
                        
                        if not where_clauses:
                            continue  # Skip if no filters
                        
                        where_sql = "WHERE " + " AND ".join(where_clauses)
                        
                        # Count first
                        cursor.execute(f"SELECT COUNT(*) FROM {table} {where_sql}", params)
                        count = cursor.fetchone()[0]
                        
                        if count > 0:
                            cursor.execute(f"DELETE FROM {table} {where_sql}", params)
                            deleted = cursor.rowcount
                            total_deleted += deleted
                            deleted_details[table] = deleted
                            connection.commit()
                
                # Audit log
                log_admin_action(
                    user["username"], 
                    "DELETE", 
                    "all_data", 
                    "pre-deletion", 
                    f"reason={request.reason}; deleted={deleted_details}"
                )
                
                return {
                    "success": True,
                    "message": f"Deleted {total_deleted} rows across {len(deleted_details)} tables",
                    "details": deleted_details
                }
            else:
                query, params = build_delete_query(request.data_type, {
                    "device_id": request.device_id,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                })
                
                # Count first
                count_query = query.replace("DELETE FROM", "SELECT COUNT(*) FROM")
                cursor.execute(count_query, params)
                count = cursor.fetchone()[0]
                
                if count == 0:
                    return {"success": True, "message": "No matching records found", "deleted": 0}
                
                # Perform deletion
                cursor.execute(query, params)
                deleted = cursor.rowcount
                connection.commit()
                
                # Audit log
                log_admin_action(
                    user["username"], 
                    "DELETE", 
                    f"data:{request.data_type}", 
                    f"count={count}", 
                    f"deleted={deleted}; reason={request.reason}"
                )
                
                return {
                    "success": True,
                    "message": f"Deleted {deleted} records from {request.data_type}",
                    "deleted": deleted
                }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete data: {error}")
    finally:
        return_connection(connection)


# ============================================================
# BACKUP & RESTORE
# ============================================================

BACKUP_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backups")


@router.get("/backups")
def list_backups(user=Depends(require_permission("reports:read"))):
    """List available backups"""
    if not os.path.exists(BACKUP_BASE_DIR):
        return {"backups": []}
    
    backups = []
    for item in sorted(os.listdir(BACKUP_BASE_DIR), reverse=True):
        item_path = os.path.join(BACKUP_BASE_DIR, item)
        if os.path.isdir(item_path):
            # Check for metadata file
            meta_path = os.path.join(item_path, "backup_metadata.json")
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    metadata = json.load(f)
            
            # Calculate size
            total_size = 0
            for root, dirs, files in os.walk(item_path):
                for f in files:
                    fp = os.path.join(root, f)
                    total_size += os.path.getsize(fp)
            
            backups.append({
                "id": item,
                "path": item_path,
                "created_at": item,  # Directory name is timestamp
                "size_bytes": total_size,
                "size_human": _format_size(total_size),
                "metadata": metadata,
                "has_database": os.path.exists(os.path.join(item_path, "database.dump")),
                "has_config": os.path.exists(os.path.join(item_path, "config")),
            })
    
    return {"backups": backups}


def _format_size(bytes_val: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


@router.post("/backup")
def create_backup(request: BackupRequest, background_tasks: BackgroundTasks, user=Depends(require_permission("system_operations"))):
    """
    Create a backup of the system.
    Supports: full, config, database, rules
    """
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Backup requires confirmation")
    
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_dir = os.path.join(BACKUP_BASE_DIR, timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_info = {
        "id": timestamp,
        "type": request.backup_type,
        "created_by": user["username"],
        "created_at": datetime.now().isoformat(),
        "description": request.description,
        "include_data": request.include_data,
        "status": "in_progress",
    }
    
    # Save initial metadata
    with open(os.path.join(backup_dir, "backup_metadata.json"), "w") as f:
        json.dump(backup_info, f, indent=2)
    
    def run_backup():
        conn = None
        try:
            success = True
            errors = []
            
            # Database backup
            if request.backup_type in ("full", "database") and request.include_data:
                try:
                    dump_path = os.path.join(backup_dir, "database.dump")
                    # Use pg_dump for PostgreSQL
                    result = subprocess.run([
                        "pg_dump", 
                        "-Fc",  # Custom format (compressed)
                        "-f", dump_path,
                        os.getenv("POSTGRES_DB", "network_monitor")
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        success = False
                        errors.append(f"Database dump failed: {result.stderr}")
                    else:
                        # Verify dump file exists and is readable
                        if os.path.exists(dump_path) and os.path.getsize(dump_path) > 0:
                            backup_info["database_size"] = os.path.getsize(dump_path)
                        else:
                            success = False
                            errors.append("Database dump file is empty or missing")
                except subprocess.TimeoutExpired:
                    success = False
                    errors.append("Database dump timed out")
                except Exception as e:
                    success = False
                    errors.append(f"Database dump error: {e}")
            
            # Config backup
            if request.backup_type in ("full", "config"):
                try:
                    config_src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
                    config_dst = os.path.join(backup_dir, "config")
                    if os.path.exists(config_src):
                        shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
                except Exception as e:
                    success = False
                    errors.append(f"Config backup error: {e}")
            
            # Rules backup (control settings)
            if request.backup_type in ("full", "rules"):
                try:
                    conn = get_connection()
                    with conn.cursor() as cursor:
                        rules_data = {}
                        for table in ["network_rules", "firewall_rules", "speed_limits", "data_limits"]:
                            cursor.execute(f"SELECT * FROM {table}")
                            rows = cursor.fetchall()
                            cols = [desc[0] for desc in cursor.description]
                            rules_data[table] = [dict(zip(cols, row)) for row in rows]
                        
                        rules_path = os.path.join(backup_dir, "rules.json")
                        with open(rules_path, "w") as f:
                            json.dump(rules_data, f, indent=2, default=str)
                except Exception as e:
                    success = False
                    errors.append(f"Rules backup error: {e}")
                finally:
                    if conn:
                        return_connection(conn)
            
            # Settings backup
            if request.backup_type in ("full", "config"):
                try:
                    conn = get_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT key, value FROM settings")
                        rows = cursor.fetchall()
                        settings = {row[0]: row[1] for row in rows}
                        
                        settings_path = os.path.join(backup_dir, "settings.json")
                        with open(settings_path, "w") as f:
                            json.dump(settings, f, indent=2)
                except Exception as e:
                    success = False
                    errors.append(f"Settings backup error: {e}")
                finally:
                    if conn:
                        return_connection(conn)
            
            # Update metadata
            backup_info["status"] = "completed" if success else "failed"
            backup_info["completed_at"] = datetime.now().isoformat()
            backup_info["errors"] = errors
            backup_info["total_size"] = sum(
                os.path.getsize(os.path.join(root, f))
                for root, dirs, files in os.walk(backup_dir)
                for f in files
            )
            
            with open(os.path.join(backup_dir, "backup_metadata.json"), "w") as f:
                json.dump(backup_info, f, indent=2, default=str)
            
            # Audit log
            log_admin_action(
                user["username"],
                "BACKUP",
                f"backup:{timestamp}",
                "none",
                f"type={request.backup_type}, success={success}, errors={len(errors)}"
            )
            
        except Exception as e:
            backup_info["status"] = "failed"
            backup_info["errors"] = [str(e)]
            backup_info["completed_at"] = datetime.now().isoformat()
            with open(os.path.join(backup_dir, "backup_metadata.json"), "w") as f:
                json.dump(backup_info, f, indent=2, default=str)
    
    background_tasks.add_task(run_backup)
    
    return {
        "success": True,
        "backup_id": timestamp,
        "status": "in_progress",
        "message": "Backup started in background. Check /api/data-management/backups for status."
    }


@router.post("/restore")
def restore_backup(request: RestoreRequest, background_tasks: BackgroundTasks, user=Depends(require_permission("system_operations"))):
    """
    Restore from a backup.
    WARNING: This will overwrite current data. Use with caution.
    """
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Restore requires explicit confirmation")
    
    backup_dir = os.path.join(BACKUP_BASE_DIR, request.backup_id)
    if not os.path.exists(backup_dir):
        raise HTTPException(status_code=404, detail=f"Backup not found: {request.backup_id}")
    
    # Verify backup integrity
    meta_path = os.path.join(backup_dir, "backup_metadata.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=400, detail="Invalid backup: missing metadata")
    
    with open(meta_path) as f:
        metadata = json.load(f)
    
    if metadata.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Backup was not completed successfully: {metadata.get('status')}")
    
    def run_restore():
        conn = None
        try:
            success = True
            errors = []
            
            # Restore database
            if request.restore_data:
                dump_path = os.path.join(backup_dir, "database.dump")
                if os.path.exists(dump_path):
                    try:
                        # Use pg_restore
                        result = subprocess.run([
                            "pg_restore",
                            "--clean",
                            "--if-exists",
                            "-d", os.getenv("POSTGRES_DB", "network_monitor"),
                            dump_path
                        ], capture_output=True, text=True, timeout=300)
                        
                        if result.returncode != 0:
                            success = False
                            errors.append(f"Database restore failed: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        success = False
                        errors.append("Database restore timed out")
                    except Exception as e:
                        success = False
                        errors.append(f"Database restore error: {e}")
                else:
                    errors.append("Database dump not found in backup")
            
            # Restore config
            config_src = os.path.join(backup_dir, "config")
            if os.path.exists(config_src):
                try:
                    config_dst = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
                    if os.path.exists(config_dst):
                        shutil.rmtree(config_dst)
                    shutil.copytree(config_src, config_dst)
                except Exception as e:
                    errors.append(f"Config restore error: {e}")
            
            # Restore settings
            settings_path = os.path.join(backup_dir, "settings.json")
            if os.path.exists(settings_path):
                try:
                    conn = get_connection()
                    with conn.cursor() as cursor:
                        with open(settings_path) as f:
                            settings = json.load(f)
                        
                        for key, value in settings.items():
                            cursor.execute("""
                                INSERT INTO settings (key, value, updated_at)
                                VALUES (%s, %s, NOW())
                                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                            """, (key, value))
                        conn.commit()
                except Exception as e:
                    errors.append(f"Settings restore error: {e}")
                finally:
                    if conn:
                        return_connection(conn)
            
            # Restore rules
            rules_path = os.path.join(backup_dir, "rules.json")
            if os.path.exists(rules_path):
                try:
                    conn = get_connection()
                    with conn.cursor() as cursor:
                        with open(rules_path) as f:
                            rules_data = json.load(f)
                        
                        for table, rows in rules_data.items():
                            if table in ["network_rules", "firewall_rules", "speed_limits", "data_limits"]:
                                # Clear existing
                                cursor.execute(f"DELETE FROM {table}")
                                # Insert restored
                                if rows:
                                    cols = list(rows[0].keys())
                                    placeholders = ", ".join(["%s"] * len(cols))
                                    for row in rows:
                                        cursor.execute(
                                            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
                                            [row[c] for c in cols]
                                        )
                        conn.commit()
                except Exception as e:
                    errors.append(f"Rules restore error: {e}")
                finally:
                    if conn:
                        return_connection(conn)
            
            # Audit log
            log_admin_action(
                user["username"],
                "RESTORE",
                f"backup:{request.backup_id}",
                "pre-restore",
                f"restore_data={request.restore_data}, success={success}, errors={len(errors)}"
            )
            
        except Exception as e:
            errors = [str(e)]
            success = False
    
    background_tasks.add_task(run_restore)
    
    return {
        "success": True,
        "backup_id": request.backup_id,
        "status": "in_progress",
        "message": "Restore started in background. This will overwrite current data."
    }


@router.delete("/backups/{backup_id}")
def delete_backup(backup_id: str, user=Depends(require_permission("system_operations"))):
    """Delete a backup"""
    backup_dir = os.path.join(BACKUP_BASE_DIR, backup_id)
    if not os.path.exists(backup_dir):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        shutil.rmtree(backup_dir)
        log_admin_action(user["username"], "DELETE", f"backup:{backup_id}", "exists", "deleted")
        return {"success": True, "message": f"Backup {backup_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {e}")


@router.get("/backups/{backup_id}/verify")
def verify_backup(backup_id: str, user=Depends(require_permission("reports:read"))):
    """Verify backup integrity"""
    backup_dir = os.path.join(BACKUP_BASE_DIR, backup_id)
    if not os.path.exists(backup_dir):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    meta_path = os.path.join(backup_dir, "backup_metadata.json")
    if not os.path.exists(meta_path):
        return {"valid": False, "error": "Missing metadata"}
    
    with open(meta_path) as f:
        metadata = json.load(f)
    
    checks = {
        "metadata": True,
        "database_dump": os.path.exists(os.path.join(backup_dir, "database.dump")),
        "config": os.path.exists(os.path.join(backup_dir, "config")),
        "rules": os.path.exists(os.path.join(backup_dir, "rules.json")),
        "settings": os.path.exists(os.path.join(backup_dir, "settings.json")),
    }
    
    # Check database dump is readable
    if checks["database_dump"]:
        dump_path = os.path.join(backup_dir, "database.dump")
        checks["database_readable"] = os.path.getsize(dump_path) > 0
        # Try to list contents with pg_restore --list
        try:
            result = subprocess.run(["pg_restore", "--list", dump_path], capture_output=True, text=True, timeout=30)
            checks["database_listable"] = result.returncode == 0
        except Exception:
            checks["database_listable"] = False
    
    all_valid = all(checks.values())
    
    return {
        "valid": all_valid,
        "checks": checks,
        "metadata": metadata,
    }