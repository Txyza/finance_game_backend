import uuid

from pydantic import BaseModel, Field


class WorkListItem(BaseModel):
    name: str = Field(max_length=2048)
    description: str
    energy: int = Field(ge=0)
    amount_booster: int = Field(ge=0)


class WorkListResponse(BaseModel):
    works: list[WorkListItem]


class WorkStartResponse(BaseModel):
    transaction_id: uuid.UUID


class WorkStopRequest(BaseModel):
    transaction_id: uuid.UUID
    points: int = Field(ge=0)


class WorkStopResponse(BaseModel):
    amount: int
