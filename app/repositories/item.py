from typing import Iterable

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item
from app.schemas import ItemCreate, ItemRead, ItemType, ItemUpdate


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ItemCreate) -> ItemRead:
        payload = data.model_dump()
        metadata = payload.pop("metadata", {})
        item = Item(**payload)
        item._metadata = metadata
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return ItemRead.model_validate(item)

    async def get(self, name: str) -> ItemRead | None:
        instance = await self._session.get(Item, name)
        if instance is None:
            return None
        return ItemRead.model_validate(instance)

    async def list_many(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        item_type: ItemType | None = None,
    ) -> list[ItemRead]:
        query: Select[tuple[Item]] = select(Item)
        if item_type is not None:
            query = query.where(Item.type == item_type)

        result = await self._session.execute(query.offset(offset).limit(limit))
        return self._map_many(result.scalars().all())

    async def update(self, name: str, data: ItemUpdate) -> ItemRead | None:
        instance = await self._session.get(Item, name)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        metadata = payload.pop("metadata", None)
        for field, value in payload.items():
            setattr(instance, field, value)

        if metadata is not None:
            instance._metadata = metadata

        await self._session.flush()
        await self._session.refresh(instance)
        return ItemRead.model_validate(instance)

    async def delete(self, name: str) -> bool:
        instance = await self._session.get(Item, name)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[Item]) -> list[ItemRead]:
        return [ItemRead.model_validate(obj) for obj in instances]
