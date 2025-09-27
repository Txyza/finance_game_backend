import uuid

from pydantic import BaseModel, Field


class WorkListItem(BaseModel):
    name: str = Field(max_length=2048)
    description: str
    energy: int = Field(ge=0)
    amount_booster: float = Field(ge=0)


class WorkListResponse(BaseModel):
    works: list[WorkListItem]


class WorkStartRequest(BaseModel):
    work_name: str = Field(max_length=2048)


class WorkStartResponse(BaseModel):
    transaction_id: uuid.UUID


class WorkStopRequest(BaseModel):
    transaction_id: uuid.UUID
    points: int = Field(ge=0)


class WorkStopResponse(BaseModel):
    amount: int
