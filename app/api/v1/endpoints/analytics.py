from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import (
    TransactionListResponse,
    TransactionSummaryCategory,
    TransactionSummaryResponse,
)
from app.api.utils import attach_items
from app.repositories import (
    ItemRepository,
    TransactionRepository,
    UserItemRepository,
)
from app.schemas.item import ItemNames, ItemType
from app.schemas.transaction import TransactionType
from app.schemas.work import WorkNames

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_user_transactions(
    current_user: CurrentUser,
    session: SessionDep,
    cursor: UUID | None = Query(
        default=None, description="Идентификатор последней транзакции"
    ),
    limit: int = Query(
        default=50, ge=1, le=100, description="Количество транзакций в ответе"
    ),
) -> TransactionListResponse:
    """Вернуть транзакции пользователя с пагинацией по курсору."""

    repository = TransactionRepository(session)
    transactions = await repository.list_by_user_cursor(
        current_user.id,
        cursor=cursor,
        limit=limit,
    )

    next_cursor: UUID | None = transactions[-1].id if transactions else None

    return TransactionListResponse(transactions=transactions, next_cursor=next_cursor)


@router.get(
    "/summary",
    response_model=TransactionSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def transaction_summary(
    current_user: CurrentUser,
    session: SessionDep,
) -> TransactionSummaryResponse:
    """Сводка доходов и расходов пользователя по типам и источникам."""

    transaction_repository = TransactionRepository(session)
    user_item_repository = UserItemRepository(session)
    item_repository = ItemRepository(session)

    transactions = await transaction_repository.list_by_user_cursor(
        current_user.id,
        limit=10_000,
    )

    user_items = await user_item_repository.list_by_user(current_user.id)
    inventory_with_items = await attach_items(user_items, item_repository)
    user_item_lookup = {
        str(user_item.id): (user_item, item) for user_item, item in inventory_with_items
    }

    income = TransactionSummaryCategory()
    expense = TransactionSummaryCategory()

    for transaction in transactions:
        if transaction.amount == 0:
            continue
        target = income if transaction.amount >= 0 else expense
        amount = transaction.amount

        match transaction.type:
            case TransactionType.WORK:
                try:
                    work_name = WorkNames(transaction.name)
                except ValueError:
                    target.other.setdefault(transaction.name, 0)
                    target.other[transaction.name] += amount
                else:
                    target.work.setdefault(work_name, 0)
                    target.work[work_name] += amount
            case TransactionType.BANK:
                instrument_key = transaction.instrument_id
                if instrument_key is None:
                    target.other.setdefault(transaction.name, 0)
                    target.other[transaction.name] += amount
                    continue

                pair = user_item_lookup.get(instrument_key)
                if pair is None:
                    target.other.setdefault(transaction.name, 0)
                    target.other[transaction.name] += amount
                    continue

                _, item = pair
                bank_type = (
                    item.type
                    if isinstance(item.type, ItemType)
                    else ItemType(item.type)
                )

                try:
                    instrument = ItemNames(item.name)
                except ValueError:
                    target.other.setdefault(item.name, 0)
                    target.other[item.name] += amount
                    continue

                target.bank.setdefault(bank_type, {})
                target.bank[bank_type].setdefault(instrument, 0)
                target.bank[bank_type][instrument] += amount
            case TransactionType.TASK:
                target.task.setdefault(transaction.name, 0)
                target.task[transaction.name] += amount
            case _:
                target.other.setdefault(transaction.name, 0)
                target.other[transaction.name] += amount

    return TransactionSummaryResponse(
        income=income,
        expense=expense,
    )
