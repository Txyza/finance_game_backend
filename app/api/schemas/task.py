import uuid

from pydantic import BaseModel

from app.schemas import TaskRead, UserTaskRead


class TaskListItem(BaseModel):
    user_task: UserTaskRead
    task: TaskRead


class TaskListResponse(BaseModel):
    tasks: list[TaskListItem]


class TaskRewardRequest(BaseModel):
    user_task_id: uuid.UUID
