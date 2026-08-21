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
)

from control.engine import ControlEngine

from database.connection import get_connection

router = APIRouter()

control_engine = ControlEngine()


class RuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    action: str = "ALLOW"
    enabled: bool = True


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


# ============================================================
# RULES
# ============================================================

@router.get("/rules")
def get_rules(user=Depends(get_current_user)):
    """Return all network rules."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, device_id, 'RULE' as name, 'Network Rule' as description,
                       'ALLOW' as action, enabled, created_at
                FROM speed_limits
                ORDER BY created_at DESC
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
                "created_at": row[6],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load rules: {error}")
    finally:
        connection.close()


@router.post("/rules")
def create_rule(rule: RuleRequest, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO speed_limits (device_id, download_limit_bps, upload_limit_bps, enabled, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (rule.name, 0, 0, rule.enabled),
            )
            row = cursor.fetchone()
            connection.commit()
        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {error}")
    finally:
        connection.close()


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, rule: RuleRequest, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE speed_limits
                SET device_id = %s, enabled = %s
                WHERE id = %s
                RETURNING id
                """,
                (rule.name, rule.enabled, rule_id),
            )
            row = cursor.fetchone()
            connection.commit()
        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update rule: {error}")
    finally:
        connection.close()


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM speed_limits WHERE id = %s", (rule_id,))
            connection.commit()
        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {error}")
    finally:
        connection.close()


# ============================================================
# LIMITS
# ============================================================

@router.get("/limits")
def get_limits(user=Depends(get_current_user)):
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
        connection.close()


@router.post("/limits")
def create_limit(limit: LimitRequest, user=Depends(get_current_user)):
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
        return {"id": row[0], "device_id": limit.device_id, "enabled": limit.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create limit: {error}")
    finally:
        connection.close()


@router.put("/limits/{limit_id}")
def update_limit(limit_id: int, limit: LimitRequest, user=Depends(get_current_user)):
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
        return {"id": row[0], "device_id": limit.device_id, "enabled": limit.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update limit: {error}")
    finally:
        connection.close()


@router.delete("/limits/{limit_id}")
def delete_limit(limit_id: int, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM speed_limits WHERE id = %s", (limit_id,))
            connection.commit()
        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete limit: {error}")
    finally:
        connection.close()


# ============================================================
# FIREWALL
# ============================================================

@router.get("/firewall")
def get_firewall(user=Depends(get_current_user)):
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
        connection.close()


@router.post("/firewall")
def create_firewall_rule(rule: FirewallRuleRequest, user=Depends(get_current_user)):
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
                (None, rule.direction, rule.protocol, rule.source_ip,
                 rule.destination_ip, rule.source_port, rule.destination_port,
                 rule.action, rule.enabled),
            )
            row = cursor.fetchone()
            connection.commit()
        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create firewall rule: {error}")
    finally:
        connection.close()


@router.put("/firewall/{rule_id}")
def update_firewall_rule(rule_id: int, rule: FirewallRuleRequest, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
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
        return {"id": row[0], "name": rule.name, "action": rule.action, "enabled": rule.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update firewall rule: {error}")
    finally:
        connection.close()


@router.delete("/firewall/{rule_id}")
def delete_firewall_rule(rule_id: int, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM firewall_rules WHERE id = %s", (rule_id,))
            connection.commit()
        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete firewall rule: {error}")
    finally:
        connection.close()


# ============================================================
# QUOTAS
# ============================================================

@router.get("/quotas")
def get_quotas(user=Depends(get_current_user)):
    """Return all device quotas."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, device_id, daily_quota_bytes, weekly_quota_bytes,
                       monthly_quota_bytes, used_bytes, reset_period, enabled,
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
                "reset_day": 1,
                "enabled": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }
            for row in rows
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to load quotas: {error}")
    finally:
        connection.close()


@router.post("/quotas")
def create_quota(quota: QuotaRequest, user=Depends(get_current_user)):
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
                    monthly_quota_bytes, used_bytes, reset_period, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 0, %s, %s, NOW(), NOW())
                ON CONFLICT (device_id)
                DO UPDATE SET
                    daily_quota_bytes = EXCLUDED.daily_quota_bytes,
                    weekly_quota_bytes = EXCLUDED.weekly_quota_bytes,
                    monthly_quota_bytes = EXCLUDED.monthly_quota_bytes,
                    reset_period = EXCLUDED.reset_period,
                    enabled = EXCLUDED.enabled,
                    updated_at = NOW()
                RETURNING id
                """,
                (quota.device_id, daily_bytes, weekly_bytes, monthly_bytes,
                 quota.reset_period or "DAILY", quota.enabled),
            )
            row = cursor.fetchone()
            connection.commit()
        return {"id": row[0], "device_id": quota.device_id, "enabled": quota.enabled}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to create quota: {error}")
    finally:
        connection.close()


@router.put("/quotas/{quota_id}")
def update_quota(quota_id: int, quota: QuotaRequest, user=Depends(get_current_user)):
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
                UPDATE data_limits
                SET device_id = %s, daily_quota_bytes = %s, weekly_quota_bytes = %s,
                    monthly_quota_bytes = %s, reset_period = %s, enabled = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                (quota.device_id, daily_bytes, weekly_bytes, monthly_bytes,
                 quota.reset_period or "DAILY", quota.enabled, quota_id),
            )
            row = cursor.fetchone()
            connection.commit()
        if not row:
            raise HTTPException(status_code=404, detail="Quota not found")
        return {"id": row[0], "device_id": quota.device_id, "enabled": quota.enabled}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to update quota: {error}")
    finally:
        connection.close()


@router.delete("/quotas/{quota_id}")
def delete_quota(quota_id: int, user=Depends(get_current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM data_limits WHERE id = %s", (quota_id,))
            connection.commit()
        return {"success": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to delete quota: {error}")
    finally:
        connection.close()
