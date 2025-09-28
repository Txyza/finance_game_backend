import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Transaction
from app.schemas import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: TransactionCreate) -> TransactionRead:
        transaction = Transaction(**data.model_dump())
        self._session.add(transaction)
        await self._session.flush()
        await self._session.refresh(transaction)
        return TransactionRead.model_validate(transaction)

    async def get(self, transaction_id: uuid.UUID) -> TransactionRead | None:
        instance = await self._session.get(Transaction, transaction_id)
        if instance is None:
            return None
        return TransactionRead.model_validate(instance)

    async def list_many(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[TransactionRead]:
        result = await self._session.execute(
            select(Transaction).offset(offset).limit(limit)
        )
        transactions = result.scalars().all()
        return self._map_many(transactions)

    async def list_by_user_cursor(
        self,
        user_id: uuid.UUID,
        *,
        cursor: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[TransactionRead]:
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.id.desc())
            .limit(limit)
        )
        if cursor is not None:
            stmt = stmt.where(Transaction.id < cursor)

        result = await self._session.execute(stmt)
        return self._map_many(result.scalars().all())

    async def update(
        self,
        transaction_id: uuid.UUID,
        data: TransactionUpdate,
    ) -> TransactionRead | None:
        instance = await self._session.get(Transaction, transaction_id)
        if instance is None:
            return None

        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in payload.items():
            setattr(instance, field, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return TransactionRead.model_validate(instance)

    async def delete(self, transaction_id: uuid.UUID) -> bool:
        instance = await self._session.get(Transaction, transaction_id)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    @staticmethod
    def _map_many(instances: Iterable[Transaction]) -> list[TransactionRead]:
        return [TransactionRead.model_validate(obj) for obj in instances]
