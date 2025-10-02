from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class WorkNames(StrEnum):
    GAME_2048 = "2048"
    MEMORY = "memory"


class WorkBase(BaseModel):
    description: str
    base_energy: int = Field(ge=0)
    max_amount: int = Field(ge=0)


class WorkCreate(WorkBase):
    name: str = Field(max_length=2048)


class WorkUpdate(BaseModel):
    description: str | None = None
    base_energy: int | None = Field(default=None, ge=0)
    max_amount: int | None = Field(default=None, ge=0)


class WorkRead(WorkBase):
    name: str

    model_config = ConfigDict(from_attributes=True)
