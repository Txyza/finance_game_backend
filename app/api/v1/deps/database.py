from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_database


async def get_db() -> AsyncSession:
    async for session in get_database():
        yield session