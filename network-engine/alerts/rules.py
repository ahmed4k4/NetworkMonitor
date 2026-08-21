from dataclasses import dataclass


@dataclass
class AlertRule:

    name: str

    enabled: bool = True

    threshold: float | None = None

    severity: str = "WARNING"