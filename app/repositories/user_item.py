import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserItem, Item
from app.schemas import UserItemCreate, UserItemRead, UserItemUpdate
from app.schemas.item import ItemType


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

    async def get_by_id(self, user_item_id: uuid.UUID) -> UserItemRead | None:
        """Alias for get method for compatibility"""
        return await self.get(user_item_id)

    async def update_amount(
        self, user_item_id: uuid.UUID, new_amount: int
    ) -> UserItemRead | None:
        """Update amount for specific user item"""
        instance = await self._session.get(UserItem, user_item_id)
        if instance is None:
            return None

        instance.amount = new_amount
        await self._session.flush()
        await self._session.refresh(instance)
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

    async def list_active_by_item_types(
        self,
        item_types: list[ItemType],
        *,
        offset: int = 0,
        limit: int = 10_000,
    ) -> list[UserItemRead]:
        """List active user items filtered by Item.type with positive amount."""
        result = await self._session.execute(
            select(UserItem)
            .join(Item, Item.name == UserItem.item_name)
            .where(Item.type.in_(item_types))
            .where(UserItem.amount > 0)
            .offset(offset)
            .limit(limit)
        )
        return self._map_many(result.scalars().all())

    async def list_active_savings_accounts(
        self, *, offset: int = 0, limit: int = 10_000
    ) -> list[UserItemRead]:
        return await self.list_active_by_item_types(
            [ItemType.SAVINGS], offset=offset, limit=limit
        )

    async def list_active_deposits(
        self, *, offset: int = 0, limit: int = 10_000
    ) -> list[UserItemRead]:
        return await self.list_active_by_item_types(
            [ItemType.DEPOSIT], offset=offset, limit=limit
        )

    async def list_savings_accounts(
        self, *, offset: int = 0, limit: int = 10_000
    ) -> list[UserItemRead]:
        """List all savings accounts (by Item.type), regardless of balance."""
        result = await self._session.execute(
            select(UserItem)
            .join(Item, Item.name == UserItem.item_name)
            .where(Item.type == ItemType.SAVINGS)
            .offset(offset)
            .limit(limit)
        )
        return self._map_many(result.scalars().all())

    async def get_first_debet_account(self, user_id: uuid.UUID) -> UserItemRead | None:
        """Return first debet (debit) account for user via Item.type join."""
        result = await self._session.execute(
            select(UserItem)
            .join(Item, Item.name == UserItem.item_name)
            .where(UserItem.user_id == user_id)
            .where(Item.type == ItemType.DEBET)
            .limit(1)
        )
        instance = result.scalar_one_or_none()
        return None if instance is None else UserItemRead.model_validate(instance)

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
