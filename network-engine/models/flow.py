from dataclasses import dataclass, field
from datetime import datetime, timezone
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

    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    packets: int = 0
    bytes: int = 0

    upload_bytes: int = 0
    download_bytes: int = 0
    
    direction: str = "UNKNOWN"
    device_id: Optional[str] = None

    state: str = "ACTIVE"
    
    # Attribution fields
    sni: Optional[str] = None
    domain: Optional[str] = None

    # Bytes already attributed to intelligence tables. Used for incremental
    # (delta) attribution of long-lived ACTIVE flows so we never double-count.
    attributed_upload_bytes: int = 0
    attributed_download_bytes: int = 0
    attributed_packets: int = 0

    # True once the flow's first/opening attribution has been recorded. Used to
    # increment the "connections"/"queries" counters only on the first delta so
    # long-lived flows do not inflate the count each attribution cycle.
    attributed_once: bool = False

    # Timestamp of the last attribution cycle for this flow. Used to compute
    # correct instantaneous speed (delta_bytes * 8 / elapsed_seconds) instead
    # of averaging over the entire flow lifetime.
    last_attributed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def duration(self) -> float:
        """Total flow lifetime in seconds (since flow creation)."""
        return (
            self.last_seen - self.started_at
        ).total_seconds()

    def attribution_elapsed(self) -> float:
        """Elapsed seconds since last attribution. For instantaneous speed calc."""
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_attributed_at).total_seconds()
        return max(0.001, elapsed)  # minimum 1ms to avoid division by zero
