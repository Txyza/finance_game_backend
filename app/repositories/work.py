from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Work
from app.schemas import WorkCreate, WorkRead, WorkUpdate


class WorkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: WorkCreate) -> WorkRead:
        work = Work(**data.model_dump())
        self._session.add(work)
        await self._session.flush()
        await self._session.refresh(work)
        return WorkRead.model_validate(work)

    async def get(self, name: str) -> WorkRead | None:
        instance = await self._session.get(Work, name)
        if instance is None:
            return None
        return WorkRead.model_validate(instance)

    async def list_many(self, *, offset: int = 0, limit: int = 100) -> list[WorkRead]:
        result = await self._session.execute(select(Work).offset(offset).limit(limit))
        return self._map_many(result.scalars().all())

    async def update(self, name: str, data: WorkUpdate) -> WorkRead | None:
        instance = await self._session.get(Work, name)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return WorkRead.model_validate(instance)

    async def delete(self, name: str) -> bool:
        instance = await self._session.get(Work, name)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[Work]) -> list[WorkRead]:
        return [WorkRead.model_validate(obj) for obj in instances]
