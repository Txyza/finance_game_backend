import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ItemUser
from app.schemas import ItemUserCreate, ItemUserRead, ItemUserUpdate


class ItemUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ItemUserCreate) -> ItemUserRead:
        item_user = ItemUser(**data.model_dump())
        self._session.add(item_user)
        await self._session.flush()
        await self._session.refresh(item_user)
        return ItemUserRead.model_validate(item_user)

    async def get(self, item_user_id: uuid.UUID) -> ItemUserRead | None:
        instance = await self._session.get(ItemUser, item_user_id)
        if instance is None:
            return None
        return ItemUserRead.model_validate(instance)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ItemUserRead]:
        result = await self._session.execute(
            select(ItemUser)
            .where(ItemUser.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        return self._map_many(result.scalars().all())

    async def update(
        self,
        item_user_id: uuid.UUID,
        data: ItemUserUpdate,
    ) -> ItemUserRead | None:
        instance = await self._session.get(ItemUser, item_user_id)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return ItemUserRead.model_validate(instance)

    async def delete(self, item_user_id: uuid.UUID) -> bool:
        instance = await self._session.get(ItemUser, item_user_id)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[ItemUser]) -> list[ItemUserRead]:
        return [ItemUserRead.model_validate(obj) for obj in instances]
