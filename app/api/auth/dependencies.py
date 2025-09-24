import uuid
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.repositories import UserRepository
from app.schemas import UserRead


async def get_uuid_by_user_agent(
    user_agent: str | None = Header(default=None, alias="User-Agent"),
) -> uuid.UUID:
    if not user_agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User-Agent header required",
        )
    return uuid.uuid5(uuid.NAMESPACE_DNS, user_agent)


async def get_current_user(
    user_id: Annotated[uuid.UUID, Depends(get_uuid_by_user_agent)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    repository = UserRepository(session)
    user = await repository.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return user
