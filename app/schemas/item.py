from enum import Enum, StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ItemType(str, Enum):
    FINANCE = "finance"
    PERMANENT = "permanent"
    DEBET = "debet"


class ItemNames(StrEnum):
    ENERGY_DRINK = "energy_drink"
    TACTICAL_PLANNER = "tactical_planner"
    RISK_SHIELD = "risk_shield"
    SMART_MIR = "smart_mir"
    SUPREME_MIR = "supreme_mir"


class ItemBase(BaseModel):
    description: str
    price: int = Field(ge=0)
    type: ItemType
    exclusive: bool = False
    energy_max_boost: float = 0.0
    energy_recovery_boost: float = 0.0
    energy_shild_boost: float = 0.0
    duration_seconds: int = Field(default=0, ge=0)
    image: str | None = None


class ItemCreate(ItemBase):
    name: str = Field(max_length=255)


class ItemUpdate(BaseModel):
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    type: ItemType | None = None
    exclusive: bool | None = None
    energy_max_boost: float | None = None
    energy_recovery_boost: float | None = None
    energy_shild_boost: float | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    image: str | None = None


class ItemRead(ItemBase):
    name: str

    model_config = ConfigDict(from_attributes=True)
