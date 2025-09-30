import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserItem
from app.schemas import UserItemCreate, UserItemRead, UserItemUpdate


class UserItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: UserItemCreate) -> UserItemRead:
        user_item = UserItem(**data.model_dump())
        self._session.add(user_item)
        await self._session.flush()
        await self._session.refresh(user_item)
        return UserItemRead.model_validate(user_item)

    async def get(self, user_item_id: uuid.UUID) -> UserItemRead | None:
        instance = await self._session.get(UserItem, user_item_id)
        if instance is None:
            return None
        return UserItemRead.model_validate(instance)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[UserItemRead]:
        now = datetime.now(timezone.utc)
        await self._delete_expired_for_user(user_id, now)

        result = await self._session.execute(
            select(UserItem)
            .where(UserItem.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        return self._map_many(result.scalars().all())

    async def update(
        self,
        user_item_id: uuid.UUID,
        data: UserItemUpdate,
    ) -> UserItemRead | None:
        instance = await self._session.get(UserItem, user_item_id)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return UserItemRead.model_validate(instance)

    async def delete(self, user_item_id: uuid.UUID) -> bool:
        instance = await self._session.get(UserItem, user_item_id)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    async def delete_expired(
        self,
        *,
        before: datetime,
        limit: int = 1_000,
    ) -> int:
        """Delete expired user items up to the provided limit."""

        stmt = (
            select(UserItem.id)
            .where(UserItem.expaired_at.is_not(None))
            .where(UserItem.expaired_at <= before)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        ids = result.scalars().all()
        if not ids:
            return 0

        await self._session.execute(delete(UserItem).where(UserItem.id.in_(ids)))
        await self._session.flush()
        return len(ids)

    @staticmethod
    def _map_many(instances: Iterable[UserItem]) -> list[UserItemRead]:
        return [UserItemRead.model_validate(obj) for obj in instances]

    async def _delete_expired_for_user(self, user_id: uuid.UUID, now: datetime) -> None:
        stmt = (
            select(UserItem.id)
            .where(UserItem.user_id == user_id)
            .where(UserItem.expaired_at.is_not(None))
            .where(UserItem.expaired_at <= now)
        )
        result = await self._session.execute(stmt)
        ids = result.scalars().all()
        if not ids:
            return

        await self._session.execute(delete(UserItem).where(UserItem.id.in_(ids)))
        await self._session.flush()
