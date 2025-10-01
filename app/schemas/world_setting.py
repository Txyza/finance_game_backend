from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class WorldSettingName(StrEnum):
    KEY_RATE = "key_rate"
    INFLATION = "inflation"
    AVG_INFLATION = "avg_inflation"


class WorldSettingBase(BaseModel):
    value: Decimal
    description: str


class WorldSettingCreate(WorldSettingBase):
    name: WorldSettingName


class WorldSettingUpdate(BaseModel):
    value: Decimal | None = None
    description: str | None = None


class WorldSettingRead(WorldSettingBase):
    name: WorldSettingName

    model_config = ConfigDict(from_attributes=True)
