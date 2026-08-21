from enum import IntEnum


class Priority(IntEnum):

    LOW = 1
    NORMAL = 2
    HIGH = 3


def get_priority(
    value: str,
) -> Priority:

    priorities = {
        "LOW": Priority.LOW,
        "NORMAL": Priority.NORMAL,
        "HIGH": Priority.HIGH,
    }

    return priorities.get(
        value.upper(),
        Priority.NORMAL,
    )