import math
from typing import Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import StoreBuyRequest, StoreItem, StoreListResponse
from app.api.utils import (
    attach_items,
    calculate_max_energy,
    find_primary_debet_item,
    is_instant_item,
)
from app.core.constants import EnergyDefaults
from app.repositories import (
    ItemRepository,
    TransactionRepository,
    UserItemRepository,
    UserRepository,
)
from app.schemas import (
    ItemNames,
    ItemType,
    ItemRead,
    TransactionCreate,
    TransactionType,
    UserItemCreate,
    UserItemUpdate,
    UserUpdate,
)

router = APIRouter(prefix="/store", tags=["store"])


@router.get("/list", response_model=StoreListResponse, status_code=status.HTTP_200_OK)
async def list_store_items(
    current_user: CurrentUser,
    session: SessionDep,
) -> StoreListResponse:
    """Retrieve the items available in the store."""

    repository = ItemRepository(session)
    items = await repository.list_many(limit=1_000)

    store_items: list[StoreItem] = []
    for item in items:
        try:
            name_enum = ItemNames(item.name)
        except ValueError:
            continue

        if item.type not in {ItemType.FINANCE, ItemType.RENT}:
            continue

        store_items.append(
            StoreItem(
                name=name_enum.value,
                description=item.description,
                price=item.price,
                image=item.image,
                exists=True,
            )
        )

    return StoreListResponse(items=store_items)


@router.post("/buy", status_code=status.HTTP_202_ACCEPTED)
async def buy_store_item(
    payload: StoreBuyRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    """Purchase an item from the store."""

    item_repository = ItemRepository(session)
    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)
    user_repository = UserRepository(session)

    try:
        item_name = ItemNames(payload.name).value
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        ) from exc

    item = await item_repository.get(item_name)
    if item is None or item.type not in {ItemType.FINANCE, ItemType.RENT}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    user_items = await user_item_repository.list_by_user(current_user.id)
    inventory_with_items = await attach_items(user_items, item_repository)

    debit_entry = find_primary_debet_item(inventory_with_items)
    if debit_entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debit card is required to buy items",
        )

    debit_user_item, _ = debit_entry
    if debit_user_item.amount < item.price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough funds",
        )

    now = datetime.now(timezone.utc)
    instant_item = is_instant_item(item)
    existing_entry = None
    if not instant_item:
        existing_entry = next(
            (entry for entry in inventory_with_items if entry[1].name == item.name),
            None,
        )

    expiration = None
    if not instant_item and item.duration_seconds > 0:
        expiration = now + timedelta(seconds=item.duration_seconds)

    if item.type == ItemType.RENT and existing_entry is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apartment rent already active",
        )

    # Deduct funds from the primary debit card before granting the item.
    await user_item_repository.update(
        debit_user_item.id,
        UserItemUpdate(amount=debit_user_item.amount - item.price),
    )

    if instant_item:
        user = await user_repository.get(current_user.id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User not found",
            )

        energy_delta = _calculate_instant_energy_delta(item)
        if energy_delta > 0:
            max_energy = calculate_max_energy(user, inventory_with_items)
            new_energy = min(user.energy + energy_delta, max_energy)
            if new_energy != user.energy:
                await user_repository.update(
                    user.id,
                    UserUpdate(energy=new_energy),
                )
    else:
        if existing_entry is None:
            await user_item_repository.create(
                UserItemCreate(
                    user_id=current_user.id,
                    item_name=item.name,
                    amount=1,
                    expaired_at=expiration,
                )
            )
        else:
            user_item, _ = existing_entry
            update_payload: dict[str, Any] = {}
            if item.exclusive:
                update_payload["amount"] = 1
            else:
                update_payload["amount"] = user_item.amount + 1

            if expiration is not None:
                current_expiration = user_item.expaired_at
                if current_expiration is None or current_expiration < expiration:
                    update_payload["expaired_at"] = expiration

            await user_item_repository.update(
                user_item.id,
                UserItemUpdate(**update_payload),
            )

    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(debit_user_item.id),
            amount=-item.price,
            datetime_start=now,
            datetime_end=now,
            type=TransactionType.BANK,
            name=item.name,
        )
    )


def _calculate_instant_energy_delta(item: ItemRead) -> int:
    if item.energy_recovery_boost <= 0:
        return 0

    base_energy = float(EnergyDefaults.MAX_ENERGY)
    delta = base_energy * (item.energy_recovery_boost / 100.0)
    return max(0, int(math.ceil(delta)))
