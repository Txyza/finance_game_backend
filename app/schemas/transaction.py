import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.transaction import TransactionType


class TransactionBase(BaseModel):
    instrument_id: str | None = Field(default=None, max_length=2048)
    amount: int = Field(ge=0)
    datetime_start: datetime
    datetime_end: datetime | None = None
    type: TransactionType
    name: str = Field(max_length=255)


class TransactionCreate(TransactionBase):
    user_id: uuid.UUID


class TransactionUpdate(BaseModel):
    instrument_id: str | None = Field(default=None, max_length=2048)
    amount: int | None = Field(default=None, ge=0)
    datetime_start: datetime | None = None
    datetime_end: datetime | None = None
    type: TransactionType | None = None
    name: str | None = Field(default=None, max_length=255)


class TransactionRead(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
