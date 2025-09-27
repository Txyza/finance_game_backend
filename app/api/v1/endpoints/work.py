import uuid
from datetime import datetime, timezone
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import (
    WorkListItem,
    WorkListResponse,
    WorkStartRequest,
    WorkStartResponse,
    WorkStopRequest,
    WorkStopResponse,
)
from app.api.utils import (
    InventoryEntry,
    apply_task_progress,
    attach_items,
    check_tasks,
    find_primary_debet_item,
)
from app.repositories import (
    ItemRepository,
    TransactionRepository,
    UserItemRepository,
    UserRepository,
    WorkRepository,
)
from app.schemas import (
    TransactionCreate,
    TransactionType,
    TransactionUpdate,
    UserItemUpdate,
    UserRead,
    UserUpdate,
    WorkRead,
)

router = APIRouter(prefix="/work", tags=["work"])


@router.get("/list", response_model=WorkListResponse, status_code=status.HTTP_200_OK)
async def list_work(
    current_user: CurrentUser,
    session: SessionDep,
) -> WorkListResponse:
    """Retrieve the list of available work activities."""

    work_repository = WorkRepository(session)
    user_item_repository = UserItemRepository(session)
    item_repository = ItemRepository(session)

    works = await work_repository.list_many(limit=1_000)
    inventory = await user_item_repository.list_by_user(current_user.id)
    inventory_with_items = await attach_items(inventory, item_repository)

    items: list[WorkListItem] = []
    for work in works:
        required_energy = _calculate_energy_cost(work, inventory_with_items)
        available_booster = min(
            work.max_amount,
            _calculate_amount_booster(current_user),
        )
        items.append(
            WorkListItem(
                name=work.name,
                description=work.description,
                energy=required_energy,
                amount_booster=available_booster,
            )
        )

    return WorkListResponse(works=items)


@router.post(
    "/start", response_model=WorkStartResponse, status_code=status.HTTP_201_CREATED
)
async def start_work(
    payload: WorkStartRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> WorkStartResponse:
    """Start a work session for the current user."""

    work_repository = WorkRepository(session)
    user_repository = UserRepository(session)
    transaction_repository = TransactionRepository(session)
    user_item_repository = UserItemRepository(session)
    item_repository = ItemRepository(session)

    work = await work_repository.get(payload.work_name)
    if work is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Work not found"
        )

    inventory = await user_item_repository.list_by_user(current_user.id)
    inventory_with_items = await attach_items(inventory, item_repository)

    energy_cost = _calculate_energy_cost(work, inventory_with_items)
    if current_user.energy < energy_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough energy to start work",
        )

    debit_entry = find_primary_debet_item(inventory_with_items)
    if debit_entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debit card is required to start work",
        )

    user_item, _ = debit_entry

    now = datetime.now(timezone.utc)
    transaction = await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(user_item.id),
            amount=0,
            datetime_start=now,
            datetime_end=None,
            type=TransactionType.WORK,
            name=work.name,
        )
    )

    await user_repository.update(
        current_user.id,
        UserUpdate(energy=current_user.energy - energy_cost),
    )

    return WorkStartResponse(transaction_id=transaction.id)


@router.post(
    "/stop",
    response_model=WorkStopResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_tasks({"daily_work_session": 1}).dependency())],
)
async def stop_work(
    payload: WorkStopRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> WorkStopResponse:
    """Complete a work session and grant rewards."""

    transaction_repository = TransactionRepository(session)
    work_repository = WorkRepository(session)
    user_item_repository = UserItemRepository(session)

    transaction = await transaction_repository.get(payload.transaction_id)
    if transaction is None or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    if transaction.type != TransactionType.WORK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction is not a work session",
        )

    if transaction.datetime_end is not None or (
        transaction.amount and transaction.amount > 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work reward already claimed",
        )

    work = await work_repository.get(transaction.name)
    if work is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Work not found"
        )

    experience_multiplier = _calculate_amount_booster(current_user)
    amount = int(min(payload.points, 10000) * experience_multiplier)

    now = datetime.now(timezone.utc)
    await transaction_repository.update(
        payload.transaction_id,
        TransactionUpdate(amount=amount, datetime_end=now),
    )

    if transaction.instrument_id is not None:
        try:
            user_item_id = uuid.UUID(transaction.instrument_id)
        except ValueError:
            user_item_id = None
        if user_item_id is not None:
            user_item = await user_item_repository.get(user_item_id)
            if user_item is not None:
                await user_item_repository.update(
                    user_item_id,
                    UserItemUpdate(amount=user_item.amount + amount),
                )

    await apply_task_progress(
        session,
        current_user,
        {"weekly_investor": amount},
    )

    return WorkStopResponse(amount=amount)


def _calculate_amount_booster(user: UserRead) -> float:
    return max(1, user.experience / 1_000 + 1)


def _calculate_energy_cost(
    work: WorkRead,
    inventory: Iterable[InventoryEntry],
) -> int:
    factor = 1.0
    for _, item in inventory:
        boost = max(0.0, min(item.energy_shild_boost, 1.0))
        factor *= 1.0 - boost

    adjusted = int(round(work.base_energy * factor))
    return max(0, adjusted)
