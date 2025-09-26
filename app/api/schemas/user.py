from decimal import Decimal
from enum import StrEnum
import uuid

from pydantic import BaseModel, Field

from app.schemas.item import ItemNames


class StarterCardName(StrEnum):
    SMART_MIR = ItemNames.SMART_MIR.value
    SUPREME_MIR = ItemNames.SUPREME_MIR.value


class UserCreateRequest(BaseModel):
    starter_card: StarterCardName


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    debet_money: int = Field(ge=0)
    capital: int = Field(ge=0)
    energy: int = Field(ge=0)
    max_energy: int = Field(ge=0)
    experience: int = Field(ge=0)
    key_rate: Decimal = Field(ge=0)
    inflation: Decimal = Field(ge=0)
