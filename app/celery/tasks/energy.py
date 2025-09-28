from __future__ import annotations

import asyncio
import logging
from typing import Final

from app.celery import celery_app
from app.core.redis import redis_client
from app.db.database import async_session_maker
from app.repositories import UserRepository
from app.schemas import UserUpdate

logger = logging.getLogger(__name__)

_ACTIVITY_KEY_PREFIX: Final[str] = "user:activity:"
_RECOVERY_AMOUNT: Final[int] = 10
_BATCH_SIZE: Final[int] = 200


@celery_app.task(name="app.celery.tasks.energy.recover_inactive_users")
def recover_inactive_users() -> int:
    """Scheduled task that restores energy for inactive users."""

    return asyncio.run(_recover_inactive_users())


async def _recover_inactive_users() -> int:
    updated = 0

    async with async_session_maker() as session:
        user_repository = UserRepository(session)

        offset = 0
        while True:
            users = await user_repository.list_many(offset=offset, limit=_BATCH_SIZE)
            if not users:
                break

            for user in users:
                key = f"{_ACTIVITY_KEY_PREFIX}{user.id}"
                if await redis_client.exists(key):
                    continue

                await user_repository.update(
                    user.id,
                    UserUpdate(energy=user.energy + _RECOVERY_AMOUNT),
                )
                updated += 1

            offset += len(users)

        await session.commit()

    if updated:
        logger.info("Recovered energy for %s inactive users", updated)
    return updated
