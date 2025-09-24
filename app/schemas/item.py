from pydantic import BaseModel, ConfigDict, Field

from app.db.models.item import ItemType


class ItemBase(BaseModel):
    description: str
    price: int = Field(ge=0)
    type: ItemType
    exclusive: bool = False
    energy_max_boost: float = 0.0
    energy_recovery_boost: float = 0.0
    energy_shild_boost: float = 0.0
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
    image: str | None = None


class ItemRead(ItemBase):
    name: str

    model_config = ConfigDict(from_attributes=True)
