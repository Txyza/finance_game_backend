from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import (
    SavingsAccountCloseResponse,
    SavingsAccountListItem,
    SavingsAccountListResponse,
    SavingsAccountOpenRequest,
    SavingsAccountOpenResponse,
    SavingsAccountOperationRequest,
    SavingsAccountTransactionsResponse,
)
from app.api.utils import attach_items
from app.repositories import ItemRepository, UserItemRepository
from app.schemas import ItemType

router = APIRouter(prefix="/savings", tags=["savings"])


@router.get("/list", response_model=SavingsAccountListResponse)
async def list_savings_accounts(
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountListResponse:
    """Return all savings accounts for the current user."""

    item_repository = ItemRepository(session)
    user_item_repository = UserItemRepository(session)

    user_items = await user_item_repository.list_by_user(current_user.id)
    inventory = await attach_items(user_items, item_repository)

    accounts: list[SavingsAccountListItem] = []
    now = datetime.now(timezone.utc)
    for user_item, item in inventory:
        if item.type != ItemType.SAVINGS:
            continue

        item_metadata = item.metadata or {}
        account_meta = user_item.meta or {}

        opened_at = _parse_datetime(account_meta.get("opened_at"), fallback=now)

        accounts.append(
            SavingsAccountListItem(
                id=user_item.id,
                item_name=item.name,
                balance=user_item.amount,
                interest_rate=_parse_interest_rate(item_metadata.get("interest_rate")),
                opened_at=opened_at,
                expires_at=user_item.expaired_at,
            )
        )

    return SavingsAccountListResponse(accounts=accounts)


@router.post(
    "/open",
    response_model=SavingsAccountOpenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_savings_account(
    payload: SavingsAccountOpenRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountOpenResponse:
    """Open a new savings account for the current user."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Savings account opening not implemented",
    )


@router.post("/{account_id}/deposit", status_code=status.HTTP_202_ACCEPTED)
async def deposit_to_savings_account(
    account_id: UUID,
    payload: SavingsAccountOperationRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    """Deposit funds from the primary debit account to the savings account."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Savings account deposit not implemented",
    )


@router.post("/{account_id}/withdraw", status_code=status.HTTP_202_ACCEPTED)
async def withdraw_from_savings_account(
    account_id: UUID,
    payload: SavingsAccountOperationRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    """Withdraw funds from the savings account to the primary debit account."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Savings account withdrawal not implemented",
    )


@router.post("/{account_id}/close", response_model=SavingsAccountCloseResponse)
async def close_savings_account(
    account_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountCloseResponse:
    """Close the savings account and transfer the remaining balance to the debit account."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Savings account closing not implemented",
    )


@router.get(
    "/{account_id}/transactions",
    response_model=SavingsAccountTransactionsResponse,
)
async def list_savings_account_transactions(
    account_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountTransactionsResponse:
    """Return transactions related to the savings account."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Savings account transactions listing not implemented",
    )


def _parse_interest_rate(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_datetime(value: Any, *, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)

    return fallback
