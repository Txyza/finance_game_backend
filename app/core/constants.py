from __future__ import annotations

from enum import IntEnum


class EnergyDefaults(IntEnum):
    MAX_ENERGY = 100
    RECOVERY_PER_INTERVAL = 10
    INACTIVITY_THRESHOLD_SECONDS = 3600


USER_ACTIVITY_KEY_PREFIX = "user:activity"

DEFAULT_STARTER_CARD_AMOUNT = 10_000

__all__ = (
    "EnergyDefaults",
    "USER_ACTIVITY_KEY_PREFIX",
    "DEFAULT_STARTER_CARD_AMOUNT",
)
