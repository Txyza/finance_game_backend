from pydantic import BaseModel, ConfigDict, Field

from app.db.models.task import RewardType, TaskType


class TaskBase(BaseModel):
    description: str
    type: TaskType
    reward: int = Field(ge=0)
    reward_type: RewardType
    progress_max_points: int = Field(ge=0)


class TaskCreate(TaskBase):
    name: str = Field(max_length=255)


class TaskUpdate(BaseModel):
    description: str | None = None
    type: TaskType | None = None
    reward: int | None = Field(default=None, ge=0)
    reward_type: RewardType | None = None
    progress_max_points: int | None = Field(default=None, ge=0)


class TaskRead(TaskBase):
    name: str

    model_config = ConfigDict(from_attributes=True)
