from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from events.types import (
    EventType,
    EventSeverity,
)


@dataclass
class Event:

    type: EventType
    severity: EventSeverity
    message: str

    device_id: Optional[str] = None

    user_id: Optional[str] = None

    metadata: Optional[dict] = None

    created_at: datetime = None

    def __post_init__(self):

        if self.created_at is None:
            self.created_at = datetime.utcnow()


class EventManager:

    def __init__(self):

        self.handlers = []

    def register(self, handler):

        self.handlers.append(handler)

    async def publish(self, event: Event):

        for handler in self.handlers:

            await handler(event)