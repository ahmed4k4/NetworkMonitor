from dataclasses import dataclass
from datetime import time


@dataclass
class Schedule:

    device_id: str

    start: time
    end: time

    action: str

    days: list[int]


class Scheduler:

    def __init__(self):

        self.schedules = []

    def add(
        self,
        schedule: Schedule,
    ):

        self.schedules.append(
            schedule
        )

    def remove(
        self,
        device_id: str,
    ):

        self.schedules = [
            s
            for s in self.schedules
            if s.device_id != device_id
        ]