import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: str = Field(min_length=3)
    energy: int = Field(default=0, ge=0)
    experience: int = Field(default=0, ge=0)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    energy: int | None = Field(default=None, ge=0)
    experience: int | None = Field(default=None, ge=0)


class UserRead(UserBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
