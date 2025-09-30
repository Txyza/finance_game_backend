from __future__ import annotations

import asyncio
import logging
from typing import Final

from app.celery import celery_app
from app.core.constants import USER_ACTIVITY_KEY_PREFIX
from app.core.redis import redis_client
from app.db.database import async_session_maker
from app.repositories import ItemRepository, UserItemRepository, UserRepository
from app.schemas import UserUpdate
from app.api.utils import (
    attach_items,
    calculate_max_energy,
    calculate_recovery_amount,
)

logger = logging.getLogger(__name__)

_ACTIVITY_KEY_PREFIX: Final[str] = f"{USER_ACTIVITY_KEY_PREFIX}:"
_BATCH_SIZE: Final[int] = 200


@celery_app.task(name="app.celery.tasks.energy.recover_inactive_users")
def recover_inactive_users() -> int:
    """Scheduled task that restores energy for inactive users."""

    return asyncio.run(_recover_inactive_users())


async def _recover_inactive_users() -> int:
    updated = 0

    async with async_session_maker() as session:
        user_repository = UserRepository(session)
        user_item_repository = UserItemRepository(session)
        item_repository = ItemRepository(session)

        offset = 0
        while True:
            users = await user_repository.list_many(offset=offset, limit=_BATCH_SIZE)
            if not users:
                break

            for user in users:
                key = f"{_ACTIVITY_KEY_PREFIX}{user.id}"
                if await redis_client.exists(key):
                    continue

                user_items = await user_item_repository.list_by_user(user.id)
                inventory_with_items = await attach_items(user_items, item_repository)
                max_energy = calculate_max_energy(user, inventory_with_items)
                if user.energy >= max_energy:
                    continue

                recovery_amount = calculate_recovery_amount(inventory_with_items)
                new_energy = min(user.energy + recovery_amount, max_energy)
                await user_repository.update(
                    user.id,
                    UserUpdate(energy=new_energy),
                )
                updated += 1

            offset += len(users)

        await session.commit()

    if updated:
        logger.info("Recovered energy for %s inactive users", updated)
    return updated
