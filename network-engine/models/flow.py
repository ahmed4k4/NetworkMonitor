from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Flow:
    key: str

    source_ip: str
    destination_ip: str

    source_port: Optional[int]
    destination_port: Optional[int]

    protocol: str
    interface: str

    started_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    packets: int = 0
    bytes: int = 0

    upload_bytes: int = 0
    download_bytes: int = 0
    
    direction: str = "UNKNOWN"
    device_id: Optional[str] = None

    state: str = "ACTIVE"

    def duration(self) -> float:
        return (
            self.last_seen - self.started_at
        ).total_seconds()
