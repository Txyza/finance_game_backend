import uuid

from pydantic import BaseModel, Field

from app.schemas import TaskType, RewardType


class TaskListItem(BaseModel):
    # TASK READ
    user_task_id: uuid.UUID
    name: str
    description: str
    type: TaskType
    reward_type: RewardType
    reward: int = Field(ge=0)
    progress_max_points: int = Field(ge=0)
    progress: int = Field(default=0, ge=0)
    rewarded: bool = False


class TaskListResponse(BaseModel):
    tasks: list[TaskListItem]


class TaskRewardRequest(BaseModel):
    user_task_id: uuid.UUID
