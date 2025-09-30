from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Final

from app.celery import celery_app
from app.db.database import async_session_maker
from app.repositories import UserItemRepository

logger = logging.getLogger(__name__)

_BATCH_SIZE: Final[int] = 500


@celery_app.task(name="app.celery.tasks.inventory.cleanup_expired_user_items")
def cleanup_expired_user_items() -> int:
    """Remove expired user items from the inventory tables."""

    return asyncio.run(_cleanup_expired_user_items())


async def _cleanup_expired_user_items() -> int:
    now = datetime.now(timezone.utc)
    processed_total = 0

    async with async_session_maker() as session:
        repository = UserItemRepository(session)

        while True:
            processed = await repository.delete_expired(before=now, limit=_BATCH_SIZE)
            if not processed:
                break
            processed_total += processed

        await session.commit()

    if processed_total:
        logger.info("Processed %s expired user items", processed_total)

    return processed_total
