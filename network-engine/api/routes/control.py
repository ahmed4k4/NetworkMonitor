from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel
from typing import Optional

from api.security import (
    require_roles,
    get_current_user,
    require_permission,
)

from control.engine import ControlEngine

from database.connection import get_connection, return_connection
from database.audit import log_admin_action

router = APIRouter()

control_engine = ControlEngine()


class RuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    action: str = "ALLOW"
    enabled: bool = True
    device_id: Optional[str] = None
    rule_type: Optional[str] = "DOMAIN"
    domain: Optional[str] = None
    schedule: Optional[str] = None
    priority: Optional[int] = 0


class LimitRequest(BaseModel):
    device_id: str
    download_limit: Optional[int] = None
    upload_limit: Optional[int] = None
    enabled: bool = True


class FirewallRuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    action: str = "ALLOW"
    direction: Optional[str] = None
    protocol: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    device_id: Optional[str] = None
    enabled: bool = True


class QuotaRequest(BaseModel):
    device_id: str
    quota_bytes: Optional[int] = None
    daily_quota_mb: Optional[float] = None
    weekly_quota_mb: Optional[float] = None
    monthly_quota_mb: Optional[float] = None
    reset_period: Optional[str] = "DAILY"
    reset_day: int = 1
    enabled: bool = True
    action: Optional[str] = "ALERT"  # BLOCK, THROTTLE, ALERT


# ============================================================
# RULES
# ============================================================

@router.get("/rules")
def get_rules(user=Depends(require_permission("control:rules:read"))):
    """Return all network rules with device name/IP joined in."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.id, r.device_id, r.name, r.description, r.action, r.enabled,
                    r.rule_type, r.domain, r.schedule, r.priority,
                    r.created_at, r.updated_at,
                    COALESCE(d.custom_name, d.hostname, '') AS device_name,
                    COALESCE(d.ip_address::text, '') AS device_ip
                FROM network_rules r
                LEFT JOIN devices d ON d.device_id = r.device_id
                ORDER BY COALESCE(r.priority, 0) DESC, r.created_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "device_id": row[1],
                "name": row[2],
                "description": row[3],
                "action": row[4],
                "enabled": row[5],
                "rule_type": row[6],
                "domain": row[7],
                "schedule": row[8],
                "priority": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "device_name": row[12],
                "device_ip": row[13],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load rules: {error}")
    finally:
        return_connection(connection)


@router.post("/rules")
def create_rule(rule: RuleRequest, user=Depends(require_permission("control:rules:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO network_rules
                    (device_id, name, description, action, enabled, rule_type, domain, schedule, priority, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (rule.device_id, rule.name, rule.description, rule.action, rule.enabled,
                 rule.rule_type, rule.domain, rule.schedule, rule.priority),
            )
            row = cursor.fetchone()
            connection.commit()
        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {error}")
    finally:
        return_connection(connection)


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, rule: RuleRequest, user=Depends(require_permission("control:rules:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT name, action, enabled FROM network_rules WHERE id = %s", (rule_id,))
            old = cursor.fetchone()
            old_desc = f"name={old[0]}, action={old[1]}, enabled={old[2]}" if old else "unknown"

            cursor.execute(
                """
                UPDATE network_rules
                SET device_id = %s, name = %s, description = %s, action = %s, enabled = %s,
                    rule_type = %s, domain = %s, schedule = %s, priority = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (rule.device_id, rule.name, rule.description, rule.action, rule.enabled,
                 rule.rule_type, rule.domain, rule.schedule, rule.priority, rule_id),
            )
            row = cursor.fetchone()
            connection.commit()
        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")

# Audit log
        log_admin_action(user["username"], "RULES", f"rule:{rule_id}", old_desc,
                        f"name={rule.name}, action={rule.action}, enabled={rule.enabled}",
                        device_id=rule.device_id)

        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update rule: {error}")
    finally:
        return_connection(connection)


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, user=Depends(require_permission("control:rules:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT name, action, enabled FROM network_rules WHERE id = %s", (rule_id,))
            old = cursor.fetchone()
            old_desc = f"name={old[0]}, action={old[1]}, enabled={old[2]}" if old else "unknown"

            cursor.execute("DELETE FROM network_rules WHERE id = %s", (rule_id,))
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "DELETE", f"rule:{rule_id}", old_desc, "deleted")

        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {error}")
    finally:
        return_connection(connection)


# ============================================================
# LIMITS
# ============================================================

@router.get("/limits")
def get_limits(user=Depends(require_permission("control:limits:read"))):
    """Return all device limits."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, device_id, download_limit_bps, upload_limit_bps, enabled, created_at, updated_at
                FROM speed_limits
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "device_id": row[1],
                "download_limit_bps": row[2],
                "upload_limit_bps": row[3],
                "download_limit": round((row[2] or 0) / (1024 * 8), 1) if row[2] else None,
                "upload_limit": round((row[3] or 0) / (1024 * 8), 1) if row[3] else None,
                "enabled": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load limits: {error}")
    finally:
        return_connection(connection)


@router.post("/limits")
def create_limit(limit: LimitRequest, user=Depends(require_permission("control:limits:write"))):
    connection = get_connection()
    try:
        # Convert KB/s to bits per second
        download_bps = None
        upload_bps = None
        if limit.download_limit is not None:
            download_bps = int(limit.download_limit * 1024 * 8)
        if limit.upload_limit is not None:
            upload_bps = int(limit.upload_limit * 1024 * 8)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO speed_limits (device_id, download_limit_bps, upload_limit_bps, enabled, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (limit.device_id, download_bps, upload_bps, limit.enabled),
            )
            row = cursor.fetchone()
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "LIMITS", f"device:{limit.device_id}", "none",
                        f"download={limit.download_limit}KB/s, upload={limit.upload_limit}KB/s, enabled={limit.enabled}")

        return {"id": row[0], "device_id": limit.device_id, "enabled": limit.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create limit: {error}")
    finally:
        return_connection(connection)


@router.put("/limits/{limit_id}")
def update_limit(limit_id: int, limit: LimitRequest, user=Depends(require_permission("control:limits:write"))):
    connection = get_connection()
    try:
        # Convert KB/s to bits per second
        download_bps = None
        upload_bps = None
        if limit.download_limit is not None:
            download_bps = int(limit.download_limit * 1024 * 8)
        if limit.upload_limit is not None:
            upload_bps = int(limit.upload_limit * 1024 * 8)

        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT device_id, download_limit_bps, upload_limit_bps, enabled FROM speed_limits WHERE id = %s", (limit_id,))
            old = cursor.fetchone()
            old_desc = f"device={old[0]}, download={old[1]}, upload={old[2]}, enabled={old[3]}" if old else "unknown"

            cursor.execute(
                """
                UPDATE speed_limits
                SET device_id = %s, download_limit_bps = %s, upload_limit_bps = %s, enabled = %s
                WHERE id = %s
                RETURNING id
                """,
                (limit.device_id, download_bps, upload_bps, limit.enabled, limit_id),
            )
            row = cursor.fetchone()
            connection.commit()
        if not row:
            raise HTTPException(status_code=404, detail="Limit not found")

        # Audit log
        log_admin_action(user["username"], "LIMITS", f"limit:{limit_id}", old_desc,
                        f"device={limit.device_id}, download={limit.download_limit}KB/s, upload={limit.upload_limit}KB/s, enabled={limit.enabled}")

        return {"id": row[0], "device_id": limit.device_id, "enabled": limit.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update limit: {error}")
    finally:
        return_connection(connection)


@router.delete("/limits/{limit_id}")
def delete_limit(limit_id: int, user=Depends(require_permission("control:limits:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT device_id, download_limit_bps, upload_limit_bps, enabled FROM speed_limits WHERE id = %s", (limit_id,))
            old = cursor.fetchone()
            old_desc = f"device={old[0]}, download={old[1]}, upload={old[2]}, enabled={old[3]}" if old else "unknown"

            cursor.execute("DELETE FROM speed_limits WHERE id = %s", (limit_id,))
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "DELETE", f"limit:{limit_id}", old_desc, "deleted")

        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete limit: {error}")
    finally:
        return_connection(connection)


# ============================================================
# FIREWALL
# ============================================================

@router.get("/firewall")
def get_firewall(user=Depends(require_permission("control:firewall:read"))):
    """Return all firewall rules."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, device_id, direction, protocol, source_ip::text,
                       destination_ip::text, source_port, destination_port,
                       action, enabled, created_at
                FROM firewall_rules
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "device_id": row[1],
                "name": f"{row[5]}:{row[7]}",
                "description": None,
                "action": row[8],
                "direction": row[2],
                "protocol": row[3],
                "source": row[4],
                "destination": row[5],
                "source_port": row[6],
                "destination_port": row[7],
                "enabled": row[9],
                "created_at": row[10],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load firewall rules: {error}")
    finally:
        return_connection(connection)


@router.post("/firewall")
def create_firewall_rule(rule: FirewallRuleRequest, user=Depends(require_permission("control:firewall:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO firewall_rules (device_id, direction, protocol, source_ip,
                    destination_ip, source_port, destination_port, action, enabled, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (rule.device_id, rule.direction, rule.protocol, rule.source_ip,
                 rule.destination_ip, rule.source_port, rule.destination_port,
                 rule.action, rule.enabled),
            )
            row = cursor.fetchone()
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "FIREWALL", f"rule:{row[0]}", "none",
                        f"action={rule.action}, direction={rule.direction}, proto={rule.protocol}, src={rule.source_ip}, dst={rule.destination_ip}")

        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create firewall rule: {error}")
    finally:
        return_connection(connection)


@router.put("/firewall/{rule_id}")
def update_firewall_rule(rule_id: int, rule: FirewallRuleRequest, user=Depends(require_permission("control:firewall:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT direction, protocol, source_ip, destination_ip, action, enabled FROM firewall_rules WHERE id = %s", (rule_id,))
            old = cursor.fetchone()
            old_desc = f"dir={old[0]}, proto={old[1]}, src={old[2]}, dst={old[3]}, action={old[4]}, enabled={old[5]}" if old else "unknown"

            cursor.execute(
                """
                UPDATE firewall_rules
                SET direction = %s, protocol = %s, source_ip = %s,
                    destination_ip = %s, source_port = %s, destination_port = %s,
                    action = %s, enabled = %s
                WHERE id = %s
                RETURNING id
                """,
                (rule.direction, rule.protocol, rule.source_ip,
                 rule.destination_ip, rule.source_port, rule.destination_port,
                 rule.action, rule.enabled, rule_id),
            )
            row = cursor.fetchone()
            connection.commit()
        if not row:
            raise HTTPException(status_code=404, detail="Firewall rule not found")

        # Audit log
        log_admin_action(user["username"], "FIREWALL", f"firewall:{rule_id}", old_desc,
                        f"action={rule.action}, direction={rule.direction}, proto={rule.protocol}, src={rule.source_ip}, dst={rule.destination_ip}, enabled={rule.enabled}")

        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update firewall rule: {error}")
    finally:
        return_connection(connection)


@router.delete("/firewall/{rule_id}")
def delete_firewall_rule(rule_id: int, user=Depends(require_permission("control:firewall:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT direction, protocol, source_ip, destination_ip, action, enabled FROM firewall_rules WHERE id = %s", (rule_id,))
            old = cursor.fetchone()
            old_desc = f"dir={old[0]}, proto={old[1]}, src={old[2]}, dst={old[3]}, action={old[4]}, enabled={old[5]}" if old else "unknown"

            cursor.execute("DELETE FROM firewall_rules WHERE id = %s", (rule_id,))
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "DELETE", f"firewall:{rule_id}", old_desc, "deleted")

        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete firewall rule: {error}")
    finally:
        return_connection(connection)


# ============================================================
# QUOTAS
# ============================================================

@router.get("/quotas")
def get_quotas(user=Depends(require_permission("control:quotas:read"))):
    """Return all device quotas."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, device_id, daily_quota_bytes, weekly_quota_bytes,
                       monthly_quota_bytes, used_bytes, reset_period, reset_day, action, enabled,
                       created_at, updated_at
                FROM data_limits
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "device_id": row[1],
                "daily_quota_bytes": row[2],
                "weekly_quota_bytes": row[3],
                "monthly_quota_bytes": row[4],
                "quota_bytes": row[2] or row[3] or row[4],
                "used_bytes": row[5],
                "reset_period": row[6],
                "reset_day": row[7],
                "action": row[8],
                "enabled": row[9],
                "created_at": row[10],
                "updated_at": row[11],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load quotas: {error}")
    finally:
        return_connection(connection)


@router.post("/quotas")
def create_quota(quota: QuotaRequest, user=Depends(require_permission("control:quotas:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            daily_bytes = None
            weekly_bytes = None
            monthly_bytes = None
            if quota.daily_quota_mb is not None:
                daily_bytes = int(quota.daily_quota_mb * 1024 * 1024)
            if quota.weekly_quota_mb is not None:
                weekly_bytes = int(quota.weekly_quota_mb * 1024 * 1024)
            if quota.monthly_quota_mb is not None:
                monthly_bytes = int(quota.monthly_quota_mb * 1024 * 1024)
            if quota.quota_bytes is not None:
                daily_bytes = quota.quota_bytes

            cursor.execute(
                """
                INSERT INTO data_limits (device_id, daily_quota_bytes, weekly_quota_bytes,
                    monthly_quota_bytes, used_bytes, reset_period, reset_day, action, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 0, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (device_id)
                DO UPDATE SET
                    daily_quota_bytes = EXCLUDED.daily_quota_bytes,
                    weekly_quota_bytes = EXCLUDED.weekly_quota_bytes,
                    monthly_quota_bytes = EXCLUDED.monthly_quota_bytes,
                    reset_period = EXCLUDED.reset_period,
                    reset_day = EXCLUDED.reset_day,
                    action = EXCLUDED.action,
                    enabled = EXCLUDED.enabled,
                    updated_at = NOW()
                RETURNING id
                """,
                (quota.device_id, daily_bytes, weekly_bytes, monthly_bytes,
                 quota.reset_period or "DAILY", quota.reset_day or 1, quota.action or "ALERT", quota.enabled),
            )
            row = cursor.fetchone()
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "QUOTAS", f"device:{quota.device_id}", "none",
                        f"daily={quota.daily_quota_mb}MB, weekly={quota.weekly_quota_mb}MB, monthly={quota.monthly_quota_mb}MB, action={quota.action}, enabled={quota.enabled}")

        return {"id": row[0], "device_id": quota.device_id, "enabled": quota.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create quota: {error}")
    finally:
        return_connection(connection)


@router.put("/quotas/{quota_id}")
def update_quota(quota_id: int, quota: QuotaRequest, user=Depends(require_permission("control:quotas:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT device_id, daily_quota_bytes, weekly_quota_bytes, monthly_quota_bytes, action, enabled FROM data_limits WHERE id = %s", (quota_id,))
            old = cursor.fetchone()
            old_desc = f"device={old[0]}, daily={old[1]}, weekly={old[2]}, monthly={old[3]}, action={old[4]}, enabled={old[5]}" if old else "unknown"

            daily_bytes = None
            weekly_bytes = None
            monthly_bytes = None
            if quota.daily_quota_mb is not None:
                daily_bytes = int(quota.daily_quota_mb * 1024 * 1024)
            if quota.weekly_quota_mb is not None:
                weekly_bytes = int(quota.weekly_quota_mb * 1024 * 1024)
            if quota.monthly_quota_mb is not None:
                monthly_bytes = int(quota.monthly_quota_mb * 1024 * 1024)
            if quota.quota_bytes is not None:
                daily_bytes = quota.quota_bytes

            cursor.execute(
                """
                UPDATE data_limits
                SET device_id = %s, daily_quota_bytes = %s, weekly_quota_bytes = %s,
                    monthly_quota_bytes = %s, reset_period = %s, reset_day = %s, action = %s, enabled = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (quota.device_id, daily_bytes, weekly_bytes, monthly_bytes,
                 quota.reset_period or "DAILY", quota.reset_day or 1, quota.action or "ALERT", quota.enabled, quota_id),
            )
            row = cursor.fetchone()
            connection.commit()
        if not row:
            raise HTTPException(status_code=404, detail="Quota not found")

        # Audit log
        log_admin_action(user["username"], "QUOTAS", f"quota:{quota_id}", old_desc,
                        f"device={quota.device_id}, daily={quota.daily_quota_mb}MB, weekly={quota.weekly_quota_mb}MB, monthly={quota.monthly_quota_mb}MB, action={quota.action}, enabled={quota.enabled}")

        return {"id": row[0], "device_id": quota.device_id, "enabled": quota.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update quota: {error}")
    finally:
        return_connection(connection)


@router.delete("/quotas/{quota_id}")
def delete_quota(quota_id: int, user=Depends(require_permission("control:quotas:write"))):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Get old values for audit
            cursor.execute("SELECT device_id, daily_quota_bytes, weekly_quota_bytes, monthly_quota_bytes, action, enabled FROM data_limits WHERE id = %s", (quota_id,))
            old = cursor.fetchone()
            old_desc = f"device={old[0]}, daily={old[1]}, weekly={old[2]}, monthly={old[3]}, action={old[4]}, enabled={old[5]}" if old else "unknown"

            cursor.execute("DELETE FROM data_limits WHERE id = %s", (quota_id,))
            connection.commit()

        # Audit log
        log_admin_action(user["username"], "DELETE", f"quota:{quota_id}", old_desc, "deleted")

        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete quota: {error}")
    finally:
        return_connection(connection)