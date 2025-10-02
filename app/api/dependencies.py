from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_session
from app.schemas import UserRead

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserRead, Depends(get_current_user)]

__all__ = ("SessionDep", "CurrentUser")
