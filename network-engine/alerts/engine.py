from events.manager import Event
from events.types import (
    EventType,
    EventSeverity,
)


class AlertEngine:

    def __init__(self, event_manager):

        self.event_manager = event_manager

    async def new_device(
        self,
        device_id: str,
    ):

        await self.event_manager.publish(
            Event(
                type=EventType.NEW_DEVICE,
                severity=EventSeverity.INFO,
                message="New device detected",
                device_id=device_id,
            )
        )

    async def device_offline(
        self,
        device_id: str,
    ):

        await self.event_manager.publish(
            Event(
                type=EventType.DEVICE_OFFLINE,
                severity=EventSeverity.WARNING,
                message="Device went offline",
                device_id=device_id,
            )
        )

    async def quota_exceeded(
        self,
        device_id: str,
    ):

        await self.event_manager.publish(
            Event(
                type=EventType.QUOTA_EXCEEDED,
                severity=EventSeverity.CRITICAL,
                message="Device quota exceeded",
                device_id=device_id,
            )
        )