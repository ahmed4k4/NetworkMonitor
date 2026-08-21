from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quota:
    device_id: str
    limit_bytes: int
    used_bytes: int = 0
    period: str = "DAILY"

    @property
    def remaining_bytes(self):

        return max(
            0,
            self.limit_bytes
            - self.used_bytes,
        )

    @property
    def exceeded(self):

        return (
            self.used_bytes
            >= self.limit_bytes
        )


class QuotaEngine:

    def __init__(self):

        self.quotas = {}

    def set_quota(
        self,
        device_id: str,
        limit_bytes: int,
        period: str = "DAILY",
    ):

        self.quotas[device_id] = Quota(
            device_id=device_id,
            limit_bytes=limit_bytes,
            period=period,
        )

    def update_usage(
        self,
        device_id: str,
        traffic_bytes: int,
    ):

        quota = self.quotas.get(
            device_id
        )

        if not quota:
            return None

        quota.used_bytes += traffic_bytes

        return quota
def quota_action(
    quota,
    action,
):

    if not quota.exceeded:
        return {
            "action": "NONE",
        }

    if action == "BLOCK":
        return {
            "action": "BLOCK",
        }

    if action == "THROTTLE":
        return {
            "action": "THROTTLE",
        }

    if action == "ALERT":
        return {
            "action": "ALERT",
        }

    return {
        "action": "NONE",
    }