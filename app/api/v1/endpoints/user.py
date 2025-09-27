from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.dependencies import get_uuid_by_user_agent
from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import UserCreateRequest, UserProfileResponse
from app.api.utils import (
    assign_initial_tasks,
    fetch_user_tasks_with_definitions,
    group_ready_to_reward_counts,
)
from app.repositories import (
    ItemRepository,
    UserItemRepository,
    UserRepository,
)
from app.schemas import (
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
        user_id, UserCreate(name=payload.name, energy=100)
    )

    await user_item_repository.create(
        UserItemCreate(
            user_id=user.id,
            item_name=stored_item.name,
            amount=10_000,
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

    debet_total = 0
    user_items = await user_item_repository.list_by_user(user.id)
    for user_item in user_items:
        item = await item_repository.get(user_item.item_name)
        if item is None:
            continue
        if item.type == ItemType.DEBET:
            debet_total += user_item.amount

    user_tasks, task_map = await fetch_user_tasks_with_definitions(session, user.id)
    ready_counts = group_ready_to_reward_counts(user_tasks, task_map)

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        debet_money=debet_total,
        capital=debet_total,
        energy=user.energy,
        max_energy=user.energy,
        experience=user.experience,
        key_rate=Decimal("0"),
        inflation=Decimal("0"),
        ready_to_reward_tasks_counts=ready_counts,
    )
