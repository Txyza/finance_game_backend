from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Final, Iterable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.items import InventoryEntry
from app.schemas import ItemType
from app.core.constants import EnergyDefaults, USER_ACTIVITY_KEY_PREFIX
from app.core.redis import redis_client
from app.repositories import UserRepository
from app.schemas import UserRead, UserUpdate

_ACTIVITY_KEY_PREFIX: Final[str] = f"{USER_ACTIVITY_KEY_PREFIX}:"
_ACTIVITY_TTL_SECONDS: Final[int] = EnergyDefaults.INACTIVITY_THRESHOLD_SECONDS


class NotEnoughEnergyError(RuntimeError):
    """Raised when user tries to spend more energy than available."""


async def spend_energy(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount: int,
) -> UserRead:
    """Deduct energy from user and record recent activity in Redis."""

    if amount <= 0:
        raise ValueError("Energy amount must be positive")

    user_repository = UserRepository(session)
    user = await user_repository.get(user_id)
    if user is None:
        raise ValueError("User not found")

    if user.energy < amount:
        raise NotEnoughEnergyError("Not enough energy to spend")

    updated_user = await user_repository.update(
        user_id,
        UserUpdate(energy=user.energy - amount),
    )
    if updated_user is None:
        raise RuntimeError("Failed to update user energy")

    key = f"{_ACTIVITY_KEY_PREFIX}{user_id}"
    await redis_client.setex(key, int(_ACTIVITY_TTL_SECONDS), "active")

    return updated_user


def calculate_max_energy(
    user: UserRead,
    inventory_with_items: Iterable[InventoryEntry],
) -> int:
    """Compute the maximum energy considering percentage boosters."""

    total_percent = 0.0
    for user_item, item in inventory_with_items:
        boost = max(0.0, item.energy_max_boost)
        if boost <= 0:
            continue

        count = _effective_item_count(user_item.amount, item.exclusive)
        if count == 0:
            continue

        total_percent += boost * count

    base_max = float(EnergyDefaults.MAX_ENERGY)
    boosted_cap = math.ceil(base_max * (1.0 + total_percent / 100.0))
    return max(boosted_cap, user.energy)


def calculate_recovery_amount(
    inventory_with_items: Iterable[InventoryEntry],
) -> int:
    """Compute passive energy recovery amount per interval using boosters."""

    total_percent = 0.0
    has_active_rent = False
    now = datetime.now(timezone.utc)
    for user_item, item in inventory_with_items:
        if item.type == ItemType.RENT:
            if user_item.expaired_at is None or user_item.expaired_at <= now:
                continue
            has_active_rent = True
            continue

        boost = max(0.0, item.energy_recovery_boost)
        if boost <= 0:
            continue

        count = _effective_item_count(user_item.amount, item.exclusive)
        if count == 0:
            continue

        total_percent += boost * count

    if not has_active_rent:
        return 0

    base_recovery = float(EnergyDefaults.RECOVERY_PER_INTERVAL)
    boosted_recovery = base_recovery * (1.0 + total_percent / 100.0)
    # Ensure at least one unit is recovered when boosters yield a fraction.
    return max(1, math.ceil(boosted_recovery))


def _effective_item_count(amount: int, exclusive: bool) -> int:
    """Return the number of stacks to apply for a booster item."""

    if amount <= 0:
        return 0
    if exclusive:
        return 1
    return amount
