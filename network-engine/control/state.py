from enum import Enum


class DeviceControlState(str, Enum):
    NORMAL = "NORMAL"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"
    LIMITED = "LIMITED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    SCHEDULED = "SCHEDULED"