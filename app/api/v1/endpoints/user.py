from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.dependencies import get_uuid_by_user_agent
from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import UserCreateRequest, UserProfileResponse
from app.api.utils import (
    assign_initial_tasks,
    attach_items,
    calculate_max_energy,
    fetch_user_tasks_with_definitions,
    group_ready_to_reward_counts,
)
from app.core.constants import DEFAULT_STARTER_CARD_AMOUNT, EnergyDefaults
from app.repositories import (
    ItemRepository,
    UserItemRepository,
    UserRepository,
    WorldSettingRepository,
)
from app.schemas import (
    ItemNames,
    ItemType,
    UserCreate,
    UserItemCreate,
    UserRead,
)

router = APIRouter(prefix="/user", tags=["user"])


@router.post(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreateRequest,
    session: SessionDep,
    user_id: Annotated[UUID, Depends(get_uuid_by_user_agent)],
) -> UserProfileResponse:
    """Register a user with the given starter card."""

    user_repository = UserRepository(session)
    item_repository = ItemRepository(session)
    user_item_repository = UserItemRepository(session)
    starter_card_name = payload.starter_card.value

    stored_item = await item_repository.get(starter_card_name)
    if stored_item is None or stored_item.type != ItemType.DEBET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid starter card",
        )

    existing_user = await user_repository.get(user_id)
    if existing_user is not None:
        return await _build_user_profile(existing_user, session)

    user = await user_repository.create_with_id(
        user_id,
        UserCreate(
            name=payload.name,
            energy=int(EnergyDefaults.MAX_ENERGY),
        ),
    )

    expires_at: datetime | None = None
    if stored_item.duration_seconds > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=stored_item.duration_seconds
        )

    await user_item_repository.create(
        UserItemCreate(
            user_id=user.id,
            item_name=stored_item.name,
            amount=DEFAULT_STARTER_CARD_AMOUNT,
            expaired_at=expires_at,
        )
    )

    apartment_item = await item_repository.get(ItemNames.APARTMENT_RENT.value)
    if apartment_item is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Apartment rent item is missing",
        )

    apartment_expiration: datetime | None = None
    if apartment_item.duration_seconds > 0:
        apartment_expiration = datetime.now(timezone.utc) + timedelta(
            seconds=apartment_item.duration_seconds
        )

    await user_item_repository.create(
        UserItemCreate(
            user_id=user.id,
            item_name=apartment_item.name,
            amount=1,
            expaired_at=apartment_expiration,
        )
    )

    await assign_initial_tasks(session, user.id)

    return await _build_user_profile(user, session)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    current_user: CurrentUser,
    session: SessionDep,
) -> UserProfileResponse:
    """Return the current authenticated user profile."""

    return await _build_user_profile(current_user, session)


async def _build_user_profile(
    user: UserRead,
    session: SessionDep,
) -> UserProfileResponse:
    item_repository = ItemRepository(session)
    user_item_repository = UserItemRepository(session)
    world_setting_repository = WorldSettingRepository(session)

    user_items = await user_item_repository.list_by_user(user.id)
    inventory_with_items = await attach_items(user_items, item_repository)

    debet_total = 0
    apartment_seconds_left = 0
    now = datetime.now(timezone.utc)
    for user_item, item in inventory_with_items:
        if item.type == ItemType.DEBET:
            debet_total += user_item.amount
        elif item.type == ItemType.RENT and user_item.expaired_at is not None:
            remaining = int((user_item.expaired_at - now).total_seconds())
            if remaining > apartment_seconds_left:
                apartment_seconds_left = max(0, remaining)

    max_energy = calculate_max_energy(user, inventory_with_items)

    user_tasks, task_map = await fetch_user_tasks_with_definitions(session, user.id)
    ready_counts = group_ready_to_reward_counts(user_tasks, task_map)

    key_rate = Decimal("0")
    inflation = Decimal("0")

    key_rate_value = await world_setting_repository.get_key_rate()
    key_rate = Decimal(str(key_rate_value))

    inflation_value = await world_setting_repository.get_inflation_rate()
    inflation = Decimal(str(inflation_value))

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        debet_money=debet_total,
        capital=debet_total,
        energy=user.energy,
        max_energy=max_energy,
        experience=user.experience,
        key_rate=key_rate,
        inflation=inflation,
        ready_to_reward_tasks_counts=ready_counts,
        apartment_seconds_left=apartment_seconds_left,
    )
