from __future__ import annotations

from typing import Final, Iterable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.items import InventoryEntry
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
    await redis_client.setex(key, _ACTIVITY_TTL_SECONDS, "active")

    return updated_user


def calculate_max_energy(
    user: UserRead,
    inventory_with_items: Iterable[InventoryEntry],
) -> int:
    """Compute the maximum energy considering boosters."""

    energy_boost = 0.0
    for user_item, item in inventory_with_items:
        boost = item.energy_max_boost
        if boost <= 0:
            continue
        if item.exclusive:
            energy_boost += boost
        else:
            energy_boost += boost * user_item.amount

    base_cap = int(EnergyDefaults.MAX_ENERGY + energy_boost)
    return max(base_cap, user.energy)
