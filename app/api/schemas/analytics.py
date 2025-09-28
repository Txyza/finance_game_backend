from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.item import ItemNames, ItemType
from app.schemas.work import WorkNames
from app.schemas.transaction import TransactionRead


class TransactionListResponse(BaseModel):
    transactions: list[TransactionRead]
    next_cursor: UUID | None = None


class TransactionSummaryCategory(BaseModel):
    work: dict[WorkNames, int] = Field(default_factory=dict)
    bank: dict[ItemType, dict[ItemNames, int]] = Field(default_factory=dict)
    task: dict[str, int] = Field(default_factory=dict)
    other: dict[str, int] = Field(default_factory=dict)


class TransactionSummaryResponse(BaseModel):
    income: TransactionSummaryCategory
    expense: TransactionSummaryCategory
