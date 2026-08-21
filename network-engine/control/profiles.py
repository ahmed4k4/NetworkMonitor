from dataclasses import dataclass
from typing import Optional


@dataclass
class Profile:
    name: str
    download_bps: Optional[int] = None
    upload_bps: Optional[int] = None
    priority: str = "NORMAL"
    blocked: bool = False


PROFILES = {

    "Unlimited": Profile(
        name="Unlimited",
    ),

    "Normal": Profile(
        name="Normal",
        download_bps=50_000_000,
        upload_bps=10_000_000,
        priority="NORMAL",
    ),

    "Guest": Profile(
        name="Guest",
        download_bps=10_000_000,
        upload_bps=2_000_000,
        priority="LOW",
    ),

    "Restricted": Profile(
        name="Restricted",
        download_bps=2_000_000,
        upload_bps=512_000,
        priority="LOW",
    ),

    "Gaming": Profile(
        name="Gaming",
        download_bps=100_000_000,
        upload_bps=20_000_000,
        priority="HIGH",
    ),
}


def get_profile(name: str) -> Profile:

    if name not in PROFILES:
        raise ValueError(
            f"Unknown profile: {name}"
        )

    return PROFILES[name]