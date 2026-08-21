from dataclasses import dataclass
from typing import Optional


@dataclass
class FirewallRule:

    name: str

    device_id: Optional[str] = None

    ip: Optional[str] = None

    mac: Optional[str] = None

    port: Optional[int] = None

    protocol: Optional[str] = None

    domain: Optional[str] = None

    application: Optional[str] = None

    category: Optional[str] = None

    action: str = "ALLOW"

    enabled: bool = True