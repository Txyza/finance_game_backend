from __future__ import annotations

from typing import cast

from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(
    cast(str, settings.REDIS_URL),
    encoding="utf-8",
    decode_responses=True,
)

__all__ = ("redis_client",)
