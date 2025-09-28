from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WorldSetting
from app.schemas import (
    WorldSettingCreate,
    WorldSettingName,
    WorldSettingRead,
    WorldSettingUpdate,
)


class WorldSettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: WorldSettingCreate) -> WorldSettingRead:
        setting = WorldSetting(**data.model_dump())
        self._session.add(setting)
        await self._session.flush()
        await self._session.refresh(setting)
        return WorldSettingRead.model_validate(setting)

    async def get(self, name: WorldSettingName) -> WorldSettingRead | None:
        instance = await self._session.get(WorldSetting, name.value)
        if instance is None:
            return None
        return WorldSettingRead.model_validate(instance)

    async def list_many(
        self, *, offset: int = 0, limit: int = 100
    ) -> list[WorldSettingRead]:
        query = select(WorldSetting).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return self._map_many(result.scalars().all())

    async def update(
        self, name: WorldSettingName, data: WorldSettingUpdate
    ) -> WorldSettingRead | None:
        instance = await self._session.get(WorldSetting, name.value)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return WorldSettingRead.model_validate(instance)

    async def delete(self, name: WorldSettingName) -> bool:
        instance = await self._session.get(WorldSetting, name.value)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[WorldSetting]) -> list[WorldSettingRead]:
        return [WorldSettingRead.model_validate(obj) for obj in instances]
