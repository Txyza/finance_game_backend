import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ItemUserBase(BaseModel):
    amount: int = Field(default=0, ge=0)
    meta: dict[str, Any] = Field(default_factory=dict)


class ItemUserCreate(ItemUserBase):
    user_id: uuid.UUID
    item_name: str = Field(max_length=255)


class ItemUserUpdate(BaseModel):
    amount: int | None = Field(default=None, ge=0)
    meta: dict[str, Any] | None = None


class ItemUserRead(ItemUserBase):
    id: uuid.UUID
    user_id: uuid.UUID
    item_name: str

    model_config = ConfigDict(from_attributes=True)
