from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional
import threading
import time

from database.repository import DeviceRepository
from database.connection import get_connection, return_connection
from logger import logger
from control.firewall import FirewallController
from control.qos import QoSController
from events.types import EventType


@dataclass
class Quota:
    device_id: str
    limit_bytes: int
    used_bytes: int = 0
    period: str = "DAILY"
    reset_day: int = 1
    action: str = "ALERT"
    enabled: bool = True

    @property
    def remaining_bytes(self):
        return max(0, self.limit_bytes - self.used_bytes)

    @property
    def exceeded(self):
        return self.used_bytes >= self.limit_bytes

    @property
    def usage_percentage(self):
        if self.limit_bytes <= 0:
            return 0
        return min(100, (self.used_bytes / self.limit_bytes) * 100)


class QuotaEngine:

    def __init__(self):
        self.quotas = {}
        self.lock = threading.Lock()
        self.firewall = FirewallController()
        self.qos = QoSController()
        self.repo = DeviceRepository()
        self._load_quotas_from_db()

    def _load_quotas_from_db(self):
        """Load all enabled quotas from database on startup"""
        try:
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT device_id, daily_quota_bytes, weekly_quota_bytes, 
                               monthly_quota_bytes, used_bytes, reset_period, 
                               reset_day, enabled
                        FROM data_limits
                        WHERE enabled = TRUE
                    """)
                    for row in cursor.fetchall():
                        device_id, daily, weekly, monthly, used, period, reset_day, enabled = row
                        
                        # Determine limit based on period
                        if period == "DAILY" and daily:
                            limit = daily
                        elif period == "WEEKLY" and weekly:
                            limit = weekly
                        elif period == "MONTHLY" and monthly:
                            limit = monthly
                        else:
                            limit = daily or weekly or monthly or 0
                        
                        if limit > 0:
                            self.quotas[device_id] = Quota(
                                device_id=device_id,
                                limit_bytes=limit,
                                used_bytes=used or 0,
                                period=period or "DAILY",
                                reset_day=reset_day or 1,
                                enabled=enabled,
                            )
            finally:
                return_connection(connection)
            logger.info(f"Loaded {len(self.quotas)} quotas from database")
        except Exception as e:
            logger.error(f"Error loading quotas from database: {e}")

    def set_quota(
        self,
        device_id: str,
        limit_bytes: int,
        period: str = "DAILY",
        reset_day: int = 1,
        action: str = "ALERT",
        enabled: bool = True,
    ):
        with self.lock:
            self.quotas[device_id] = Quota(
                device_id=device_id,
                limit_bytes=limit_bytes,
                period=period,
                reset_day=reset_day,
                action=action,
                enabled=enabled,
            )
            # Persist to database
            try:
                self.repo.save_device_quota(
                    device_id=device_id,
                    daily_quota_bytes=limit_bytes if period == "DAILY" else None,
                    weekly_quota_bytes=limit_bytes if period == "WEEKLY" else None,
                    monthly_quota_bytes=limit_bytes if period == "MONTHLY" else None,
                    reset_period=period,
                    enabled=enabled,
                )
            except Exception as e:
                logger.error(f"Error saving quota to database: {e}")

    def update_usage(
        self,
        device_id: str,
        traffic_bytes: int,
    ) -> Optional[Quota]:
        with self.lock:
            quota = self.quotas.get(device_id)
            
            if not quota or not quota.enabled:
                return None

            quota.used_bytes += traffic_bytes

            # Persist usage to database
            try:
                self.repo.update_quota_usage(device_id, quota.used_bytes)
            except Exception as e:
                logger.error(f"Error updating quota usage in database: {e}")

            # Check if quota exceeded and take action
            if quota.exceeded:
                self._enforce_quota(quota)

            return quota

    def _enforce_quota(self, quota: Quota):
        """Enforce quota action when exceeded"""
        try:
            if quota.action == "BLOCK":
                self._block_device(quota.device_id)
            elif quota.action == "THROTTLE":
                self._throttle_device(quota.device_id)
            elif quota.action == "ALERT":
                self._generate_alert(quota)
        except Exception as e:
            logger.error(f"Error enforcing quota for {quota.device_id}: {e}")

    def _block_device(self, device_id: str):
        """Block device via firewall"""
        try:
            # Get device IP
            device = self.repo.get_device(device_id)
            if device and device.get("ip"):
                self.firewall.block_device(device_id, device["ip"])
                logger.warning(f"QUOTA ENFORCEMENT: Blocked device {device_id} ({device['ip']})")
                self._create_quota_event(device_id, "QUOTA_EXCEEDED_BLOCKED", 
                    f"Device blocked due to quota exceeded ({quota.usage_percentage:.1f}% used)")
        except Exception as e:
            logger.error(f"Error blocking device {device_id}: {e}")

    def _throttle_device(self, device_id: str):
        """Throttle device to very low bandwidth"""
        try:
            device = self.repo.get_device(device_id)
            if device and device.get("ip"):
                # Apply severe throttle: 64 KB/s download, 16 KB/s upload
                throttle_dl = 64 * 1024 * 8  # 64 KB/s in bps
                throttle_ul = 16 * 1024 * 8  # 16 KB/s in bps
                self.qos.set_limit(device_id, device["ip"], "DOWNLOAD", throttle_dl)
                self.qos.set_limit(device_id, device["ip"], "UPLOAD", throttle_ul)
                logger.warning(f"QUOTA ENFORCEMENT: Throttled device {device_id} ({device['ip']})")
                self._create_quota_event(device_id, "QUOTA_EXCEEDED_THROTTLED",
                    f"Device throttled due to quota exceeded ({quota.usage_percentage:.1f}% used)")
        except Exception as e:
            logger.error(f"Error throttling device {device_id}: {e}")

    def _generate_alert(self, quota: Quota):
        """Generate alert in database"""
        try:
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO alerts (device_id, alert_type, severity, message, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (
                        quota.device_id,
                        "QUOTA_EXCEEDED",
                        "WARNING",
                        f"Data quota exceeded: {quota.used_bytes:,} / {quota.limit_bytes:,} bytes ({quota.usage_percentage:.1f}%)"
                    ))
                connection.commit()
            finally:
                return_connection(connection)
            logger.warning(f"QUOTA ALERT: Device {quota.device_id} exceeded quota ({quota.usage_percentage:.1f}%)")
            self._create_quota_event(quota.device_id, "QUOTA_EXCEEDED_ALERT",
                f"Quota exceeded: {quota.usage_percentage:.1f}% used")
        except Exception as e:
            logger.error(f"Error generating quota alert: {e}")

    def _create_quota_event(self, device_id: str, event_type: str, message: str):
        """Create event for quota enforcement action"""
        try:
            from events.broadcaster import broadcast_event
            broadcast_event(event_type, {
                "device_id": device_id,
                "message": message,
            })
        except Exception as e:
            logger.error(f"Error broadcasting quota event: {e}")

    def check_and_reset_quotas(self):
        """Check and reset quotas based on their period"""
        with self.lock:
            now = datetime.now()
            current_date = now.date()
            
            for device_id, quota in self.quotas.items():
                if not quota.enabled:
                    continue
                
                should_reset = False
                
                if quota.period == "DAILY":
                    # Reset daily at midnight
                    # We track the last reset date in the database
                    should_reset = self._should_reset_daily(quota, current_date)
                elif quota.period == "WEEKLY":
                    # Reset weekly on reset_day (1=Monday, 7=Sunday)
                    should_reset = self._should_reset_weekly(quota, current_date)
                elif quota.period == "MONTHLY":
                    # Reset monthly on reset_day
                    should_reset = self._should_reset_monthly(quota, current_date)
                
                if should_reset:
                    self._reset_quota(quota)

    def _should_reset_daily(self, quota: Quota, current_date: date) -> bool:
        """Check if daily quota should reset"""
        try:
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT updated_at FROM data_limits WHERE device_id = %s
                    """, (quota.device_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        last_reset = row[0].date()
                        return last_reset < current_date
            finally:
                return_connection(connection)
        except Exception as e:
            logger.error(f"Error checking daily reset: {e}")
        return False

    def _should_reset_weekly(self, quota: Quota, current_date: date) -> bool:
        """Check if weekly quota should reset"""
        try:
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT updated_at FROM data_limits WHERE device_id = %s
                    """, (quota.device_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        last_reset = row[0].date()
                        days_since = (current_date - last_reset).days
                        # Reset on the configured day of week (1=Monday)
                        current_weekday = current_date.weekday() + 1  # 1=Monday
                        if current_weekday == quota.reset_day and days_since >= 7:
                            return True
            finally:
                return_connection(connection)
        except Exception as e:
            logger.error(f"Error checking weekly reset: {e}")
        return False

    def _should_reset_monthly(self, quota: Quota, current_date: date) -> bool:
        """Check if monthly quota should reset"""
        try:
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT updated_at FROM data_limits WHERE device_id = %s
                    """, (quota.device_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        last_reset = row[0].date()
                        # Reset on the configured day of month
                        if current_date.day == quota.reset_day and current_date > last_reset:
                            return True
            finally:
                return_connection(connection)
        except Exception as e:
            logger.error(f"Error checking monthly reset: {e}")
        return False

    def _reset_quota(self, quota: Quota):
        """Reset quota usage to zero"""
        quota.used_bytes = 0
        try:
            self.repo.update_quota_usage(quota.device_id, 0)
            logger.info(f"Quota reset for device {quota.device_id} (period: {quota.period})")
            self._create_quota_event(quota.device_id, "QUOTA_RESET",
                f"Quota reset for new {quota.period.lower()} period")
        except Exception as e:
            logger.error(f"Error resetting quota: {e}")

    def get_quota(self, device_id: str) -> Optional[Quota]:
        """Get quota for a device"""
        with self.lock:
            return self.quotas.get(device_id)

    def get_all_quotas(self) -> dict:
        """Get all quotas"""
        with self.lock:
            return dict(self.quotas)

    def remove_quota(self, device_id: str):
        """Remove quota for a device"""
        with self.lock:
            if device_id in self.quotas:
                del self.quotas[device_id]
                try:
                    self.repo.delete_device_quota(device_id)
                except Exception as e:
                    logger.error(f"Error deleting quota from database: {e}")

    def disable_quota(self, device_id: str):
        """Disable quota for a device"""
        with self.lock:
            if device_id in self.quotas:
                self.quotas[device_id].enabled = False
                try:
                    self.repo.save_device_quota(device_id=device_id, enabled=False)
                except Exception as e:
                    logger.error(f"Error disabling quota: {e}")

    def enable_quota(self, device_id: str):
        """Enable quota for a device"""
        with self.lock:
            if device_id in self.quotas:
                self.quotas[device_id].enabled = True
                try:
                    self.repo.save_device_quota(device_id=device_id, enabled=True)
                except Exception as e:
                    logger.error(f"Error enabling quota: {e}")


def quota_action(quota: Quota, action: str) -> dict:
    """Legacy function for backward compatibility"""
    if not quota.exceeded:
        return {"action": "NONE"}

    if action == "BLOCK":
        return {"action": "BLOCK"}
    if action == "THROTTLE":
        return {"action": "THROTTLE"}
    if action == "ALERT":
        return {"action": "ALERT"}

    return {"action": "NONE"}