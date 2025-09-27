from __future__ import annotations

import random
import uuid
from collections import defaultdict
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import TaskRepository, UserTaskRepository
from app.schemas import TaskRead, TaskType, UserTaskCreate

_TASKS_PER_CATEGORY = 3
_FORCED_TASKS: dict[TaskType, set[str]] = {
    TaskType.DAELY: {"daily_work_session", "daily_budget_check"},
    TaskType.WEAKLY: {"weekly_investor", "weekly_collector"},
    TaskType.QUEST: set(),
}


def _group_tasks_by_type(tasks: Iterable[TaskRead]) -> dict[TaskType, list[TaskRead]]:
    buckets: dict[TaskType, list[TaskRead]] = defaultdict(list)
    for task in tasks:
        buckets[task.type].append(task)
    return buckets


def _select_tasks_for_type(
    available: list[TaskRead],
    task_type: TaskType,
) -> list[TaskRead]:
    if not available:
        return []

    forced_names = _FORCED_TASKS.get(task_type, set())
    chosen: list[TaskRead] = [task for task in available if task.name in forced_names]

    chosen_names = {task.name for task in chosen}
    remaining = [task for task in available if task.name not in chosen_names]
    needed = max(0, _TASKS_PER_CATEGORY - len(chosen))

    if needed > 0 and remaining:
        sample_size = min(needed, len(remaining))
        sampled = random.sample(remaining, sample_size)
        chosen.extend(sampled)
        chosen_names.update(task.name for task in sampled)
        remaining = [task for task in remaining if task.name not in chosen_names]

    if len(chosen) < _TASKS_PER_CATEGORY and remaining:
        missing = _TASKS_PER_CATEGORY - len(chosen)
        chosen.extend(remaining[:missing])

    return chosen[:_TASKS_PER_CATEGORY]


async def assign_initial_tasks(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Назначить пользователю стартовый набор задач."""

    user_task_repository = UserTaskRepository(session)
    existing = await user_task_repository.list_by_user(user_id, limit=1)
    if existing:
        return

    task_repository = TaskRepository(session)
    tasks = await task_repository.list_many(limit=1_000)
    tasks_by_type = _group_tasks_by_type(tasks)

    selected_tasks: list[TaskRead] = []
    for task_type in TaskType:
        bucket = tasks_by_type.get(task_type, [])
        selected_tasks.extend(_select_tasks_for_type(bucket, task_type))

    for task in selected_tasks:
        await user_task_repository.create(
            UserTaskCreate(user_id=user_id, task_name=task.name)
        )
