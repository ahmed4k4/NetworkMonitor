from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    id: str
    mac: str

    ip: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    interface: Optional[str] = None

    state: str = "UNKNOWN"

    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    bytes_sent: int = 0
    bytes_received: int = 0

    packets_sent: int = 0
    packets_received: int = 0