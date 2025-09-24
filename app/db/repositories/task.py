from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task
from app.schemas import TaskCreate, TaskRead, TaskUpdate


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: TaskCreate) -> TaskRead:
        task = Task(**data.model_dump())
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return TaskRead.model_validate(task)

    async def get(self, name: str) -> TaskRead | None:
        instance = await self._session.get(Task, name)
        if instance is None:
            return None
        return TaskRead.model_validate(instance)

    async def list_many(self, *, offset: int = 0, limit: int = 100) -> list[TaskRead]:
        result = await self._session.execute(select(Task).offset(offset).limit(limit))
        return self._map_many(result.scalars().all())

    async def update(self, name: str, data: TaskUpdate) -> TaskRead | None:
        instance = await self._session.get(Task, name)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return TaskRead.model_validate(instance)

    async def delete(self, name: str) -> bool:
        instance = await self._session.get(Task, name)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[Task]) -> list[TaskRead]:
        return [TaskRead.model_validate(obj) for obj in instances]
