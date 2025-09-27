from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import TaskListItem
from app.repositories import TaskRepository, UserTaskRepository
from app.schemas import TaskRead, TaskType, UserTaskRead


async def build_task_list(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    task_type: TaskType | None = None,
) -> list[TaskListItem]:
    user_task_repository = UserTaskRepository(session)
    task_repository = TaskRepository(session)

    user_tasks = await user_task_repository.list_by_user(user_id, limit=500)
    tasks = await task_repository.list_many(limit=1_000)
    task_map = {task.name: task for task in tasks}

    items: list[TaskListItem] = []
    for user_task in user_tasks:
        task = task_map.get(user_task.task_name)
        if task is None:
            continue
        if task_type is not None and task.type != task_type:
            continue

        items.append(_make_item(user_task, task))

    return items


def _make_item(user_task: UserTaskRead, task: TaskRead) -> TaskListItem:
    return TaskListItem(
        user_task_id=user_task.id,
        name=task.name,
        description=task.description,
        type=task.type,
        reward_type=task.reward_type,
        reward=task.reward,
        progress_max_points=task.progress_max_points,
        progress=user_task.progress,
        rewarded=user_task.rewarded,
    )
