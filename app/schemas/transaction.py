import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(str, Enum):
    BANK = "bank"
    EVENT = "event"
    WORK = "work"
    TASK = "task"
    SAVINGS_DEPOSIT = "savings_deposit"
    SAVINGS_WITHDRAWAL = "savings_withdrawal"
    SAVINGS_INTEREST = "savings_interest"
    DEPOSIT_OPEN = "deposit_open"
    DEPOSIT_CLOSE_EARLY = "deposit_close_early"
    DEPOSIT_CLOSE_MATURED = "deposit_close_matured"
    DEPOSIT_INTEREST_PAYMENT = "deposit_interest_payment"


class TransactionBase(BaseModel):
    instrument_id: str | None = Field(default=None, max_length=2048)
    amount: int
    datetime_start: datetime
    datetime_end: datetime | None = None
    type: TransactionType
    name: str = Field(max_length=255)


class TransactionCreate(TransactionBase):
    user_id: uuid.UUID


class TransactionUpdate(BaseModel):
    instrument_id: str | None = Field(default=None, max_length=2048)
    amount: int | None = Field(default=None)
    datetime_start: datetime | None = None
    datetime_end: datetime | None = None
    type: TransactionType | None = None
    name: str | None = Field(default=None, max_length=255)


class TransactionRead(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
