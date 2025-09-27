from __future__ import annotations

import uuid
from collections import Counter
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import TaskRepository, UserTaskRepository
from app.schemas import TaskRead, TaskType, UserTaskRead


async def fetch_user_tasks_with_definitions(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> tuple[list[UserTaskRead], dict[str, TaskRead]]:
    user_task_repository = UserTaskRepository(session)
    task_repository = TaskRepository(session)

    user_tasks = await user_task_repository.list_by_user(user_id, limit=500)
    tasks = await task_repository.list_many(limit=1_000)
    task_map = {task.name: task for task in tasks}
    return user_tasks, task_map


def group_ready_to_reward_counts(
    user_tasks: Iterable[UserTaskRead],
    task_map: dict[str, TaskRead],
) -> dict[TaskType, int]:
    buckets: Counter[TaskType] = Counter()
    for user_task in user_tasks:
        if user_task.rewarded:
            continue
        task = task_map.get(user_task.task_name)
        if task is None:
            continue
        if user_task.progress >= task.progress_max_points:
            buckets[task.type] += 1
    return dict(buckets)
