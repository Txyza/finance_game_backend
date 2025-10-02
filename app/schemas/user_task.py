import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserTaskBase(BaseModel):
    progress: int = Field(default=0, ge=0)
    rewarded: bool = False


class UserTaskCreate(UserTaskBase):
    user_id: uuid.UUID
    task_name: str = Field(max_length=255)


class UserTaskUpdate(BaseModel):
    progress: int | None = Field(default=None, ge=0)
    rewarded: bool | None = None


class UserTaskRead(UserTaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    task_name: str

    model_config = ConfigDict(from_attributes=True)
