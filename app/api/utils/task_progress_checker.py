from __future__ import annotations

import inspect
from functools import wraps
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Iterable,
    ParamSpec,
    TypeVar,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, SessionDep
from app.repositories import UserTaskRepository
from app.schemas import UserRead

P = ParamSpec("P")
R = TypeVar("R")
ProgressMap = dict[str, int]


async def apply_task_progress(
    session: AsyncSession,
    user: UserRead,
    progress_map: ProgressMap,
) -> None:
    repository = UserTaskRepository(session)
    for task_name, amount in progress_map.items():
        if amount <= 0:
            continue
        await repository.increment_progress(user.id, task_name, amount)


class _TaskProgressDecorator:
    def __init__(self, progress_map: ProgressMap) -> None:
        self._progress_map = progress_map

    def __call__(self, func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("check_tasks can decorate only async callables")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = inspect.signature(func).bind_partial(*args, **kwargs)
            session = _first_instance(bound.arguments.values(), AsyncSession)
            user = _first_instance(bound.arguments.values(), UserRead)
            if session is None or user is None:
                raise RuntimeError(
                    "check_tasks decorator requires AsyncSession and UserRead arguments"
                )

            result = await func(*args, **kwargs)
            await apply_task_progress(session, user, self._progress_map)
            return result

        return wrapper

    def dependency(
        self,
    ) -> Callable[[SessionDep, CurrentUser], AsyncGenerator[None, None]]:
        async def dependency_impl(
            session: SessionDep,
            current_user: CurrentUser,
        ) -> AsyncGenerator[None, None]:
            try:
                yield
            except Exception:  # pragma: no cover
                raise
            else:
                await apply_task_progress(session, current_user, self._progress_map)

            return

        return dependency_impl


def check_tasks(progress_map: ProgressMap) -> _TaskProgressDecorator:
    return _TaskProgressDecorator(progress_map)


def _first_instance(values: Iterable[Any], expected_type: type[R]) -> R | None:
    for value in values:
        if isinstance(value, expected_type):
            return value
    return None
