import uuid

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    starter_card: str = Field(..., max_length=255)


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    debet_money: int = Field(ge=0)
    capital: int = Field(ge=0)
    energy: int = Field(ge=0)
    experience: int = Field(ge=0)
