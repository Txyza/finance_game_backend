from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import TaskListResponse, TaskRewardRequest
from app.api.utils import (
    attach_items,
    build_task_list,
    check_tasks,
    find_primary_debet_item,
)
from app.repositories import (
    ItemRepository,
    TaskRepository,
    TransactionRepository,
    UserItemRepository,
    UserRepository,
    UserTaskRepository,
)
from app.schemas import (
    RewardType,
    TaskType,
    TransactionCreate,
    TransactionType,
    UserItemUpdate,
    UserUpdate,
    UserTaskUpdate,
)

router = APIRouter(prefix="/task", tags=["task"])


@router.get("/list", response_model=TaskListResponse, status_code=status.HTTP_200_OK)
async def list_tasks(
    current_user: CurrentUser,
    session: SessionDep,
    task_type: TaskType | None = None,
) -> TaskListResponse:
    """Return the list of tasks paired with user progress."""

    tasks = await build_task_list(
        session,
        current_user.id,
        task_type=task_type,
    )

    return TaskListResponse(tasks=tasks)


@router.post(
    "/get_reward",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(check_tasks({"weekly_collector": 1}).dependency())],
)
async def get_task_reward(
    payload: TaskRewardRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    """Mark the task reward as claimed for the provided progress entry."""

    user_task_repository = UserTaskRepository(session)
    task_repository = TaskRepository(session)
    transaction_repository = TransactionRepository(session)
    user_item_repository = UserItemRepository(session)
    item_repository = ItemRepository(session)
    user_repository = UserRepository(session)

    user_task = await user_task_repository.get(payload.user_task_id)
    if user_task is None or user_task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task progress not found"
        )

    if user_task.rewarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reward already claimed",
        )

    task = await task_repository.get(user_task.task_name)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if user_task.progress != task.progress_max_points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not completed",
        )

    if task.reward_type == RewardType.MONEY:
        inventory = await user_item_repository.list_by_user(current_user.id)
        inventory_with_items = await attach_items(inventory, item_repository)
        debit_entry = find_primary_debet_item(inventory_with_items)
        if debit_entry is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debit card is required to receive reward",
            )

        user_item, _ = debit_entry
        await user_item_repository.update(
            user_item.id,
            UserItemUpdate(amount=user_item.amount + task.reward),
        )

        now = datetime.now(timezone.utc)
        await transaction_repository.create(
            TransactionCreate(
                user_id=current_user.id,
                instrument_id=str(user_item.id),
                amount=task.reward,
                datetime_start=now,
                datetime_end=now,
                type=TransactionType.TASK,
                name=task.name,
            )
        )
    elif task.reward_type == RewardType.EXP:
        await user_repository.update(
            current_user.id,
            UserUpdate(experience=current_user.experience + task.reward),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported reward type",
        )

    await user_task_repository.update(
        payload.user_task_id,
        UserTaskUpdate(rewarded=True),
    )
