import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserTask
from app.schemas import UserTaskCreate, UserTaskRead, UserTaskUpdate


class UserTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: UserTaskCreate) -> UserTaskRead:
        user_task = UserTask(**data.model_dump())
        self._session.add(user_task)
        await self._session.flush()
        await self._session.refresh(user_task)
        return UserTaskRead.model_validate(user_task)

    async def get(self, user_task_id: uuid.UUID) -> UserTaskRead | None:
        instance = await self._session.get(UserTask, user_task_id)
        if instance is None:
            return None
        return UserTaskRead.model_validate(instance)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[UserTaskRead]:
        result = await self._session.execute(
            select(UserTask)
            .where(UserTask.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        return self._map_many(result.scalars().all())

    async def update(
        self,
        user_task_id: uuid.UUID,
        data: UserTaskUpdate,
    ) -> UserTaskRead | None:
        instance = await self._session.get(UserTask, user_task_id)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return UserTaskRead.model_validate(instance)

    async def delete(self, user_task_id: uuid.UUID) -> bool:
        instance = await self._session.get(UserTask, user_task_id)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    async def increment_progress(
        self,
        user_id: uuid.UUID,
        task_name: str,
        amount: int,
    ) -> bool:
        if amount <= 0:
            return False

        result = await self._session.execute(
            select(UserTask)
            .where(UserTask.user_id == user_id, UserTask.task_name == task_name)
            .limit(1)
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            return False

        instance.progress += amount
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[UserTask]) -> list[UserTaskRead]:
        return [UserTaskRead.model_validate(obj) for obj in instances]
