import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserItemBase(BaseModel):
    amount: int = Field(default=0, ge=0)
    meta: dict[str, Any] = Field(default_factory=dict)
    expaired_at: datetime | None = None


class UserItemCreate(UserItemBase):
    user_id: uuid.UUID
    item_name: str = Field(max_length=255)


class UserItemUpdate(BaseModel):
    amount: int | None = Field(default=None, ge=0)
    meta: dict[str, Any] | None = None
    expaired_at: datetime | None = None


class UserItemRead(UserItemBase):
    id: uuid.UUID
    user_id: uuid.UUID
    item_name: str

    model_config = ConfigDict(from_attributes=True)
