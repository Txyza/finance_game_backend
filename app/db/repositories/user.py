import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas import UserCreate, UserRead, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: UserCreate) -> UserRead:
        user = User(**data.model_dump())
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return UserRead.model_validate(user)

    async def create_with_id(self, user_id: uuid.UUID, data: UserCreate) -> UserRead:
        user = User(id=user_id, **data.model_dump())
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return UserRead.model_validate(user)

    async def get(self, user_id: uuid.UUID) -> UserRead | None:
        instance = await self._session.get(User, user_id)
        if instance is None:
            return None
        return UserRead.model_validate(instance)

    async def list_many(self, *, offset: int = 0, limit: int = 100) -> list[UserRead]:
        result = await self._session.execute(select(User).offset(offset).limit(limit))
        users = result.scalars().all()
        return [UserRead.model_validate(user) for user in users]

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> UserRead | None:
        instance = await self._session.get(User, user_id)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return UserRead.model_validate(instance)

    async def delete(self, user_id: uuid.UUID) -> bool:
        instance = await self._session.get(User, user_id)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True
