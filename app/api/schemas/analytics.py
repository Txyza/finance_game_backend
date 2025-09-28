from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.item import ItemNames, ItemType
from app.schemas.work import WorkNames
from app.schemas.transaction import TransactionRead


class TransactionListResponse(BaseModel):
    transactions: list[TransactionRead]
    next_cursor: UUID | None = None


class TransactionSummaryCategory(BaseModel):
    work: dict[WorkNames, Decimal] = Field(default_factory=dict)
    bank: dict[ItemType, dict[ItemNames, Decimal]] = Field(default_factory=dict)
    task: dict[str, Decimal] = Field(default_factory=dict)
    other: dict[str, Decimal] = Field(default_factory=dict)


class TransactionSummaryResponse(BaseModel):
    income: TransactionSummaryCategory
    expense: TransactionSummaryCategory
