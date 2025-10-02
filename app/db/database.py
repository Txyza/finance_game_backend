from typing import AsyncGenerator, cast
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

DATABASE_URL = cast(str, settings.DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG, future=True)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
