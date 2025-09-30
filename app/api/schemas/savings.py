import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SavingsAccountMeta(BaseModel):
    interest_rate: float = Field(ge=0)
    capitalization_period_days: int | None = Field(default=None, ge=1)
    currency: str | None = None


class SavingsAccountListItem(BaseModel):
    id: uuid.UUID
    item_name: str
    balance: int = Field(ge=0)
    interest_rate: float = Field(ge=0)
    opened_at: datetime
    expires_at: datetime | None = None


class SavingsAccountListResponse(BaseModel):
    accounts: list[SavingsAccountListItem]


class SavingsAccountOpenRequest(BaseModel):
    item_name: str = Field(max_length=255)
    initial_deposit: int = Field(default=0, ge=0)


class SavingsAccountOpenResponse(BaseModel):
    account_id: uuid.UUID


class SavingsAccountOperationRequest(BaseModel):
    amount: int = Field(gt=0)


class SavingsAccountCloseResponse(BaseModel):
    account_id: uuid.UUID
    transferred_amount: int = Field(ge=0)


class SavingsAccountTransaction(BaseModel):
    id: uuid.UUID
    amount: int
    datetime_start: datetime
    datetime_end: datetime | None = None
    type: str
    description: str | None = None


class SavingsAccountTransactionsResponse(BaseModel):
    account_id: uuid.UUID
    transactions: list[SavingsAccountTransaction]
