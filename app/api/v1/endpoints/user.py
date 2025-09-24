from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.auth.dependencies import get_uuid_by_user_agent
from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import UserCreateRequest, UserProfileResponse
from app.db.repositories import UserRepository
from app.schemas import UserCreate, UserRead

router = APIRouter(prefix="/user", tags=["user"])


@router.post(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    _payload: UserCreateRequest,
    session: SessionDep,
    user_id: Annotated[UUID, Depends(get_uuid_by_user_agent)],
) -> UserProfileResponse:
    """Register a user with the given starter card."""

    repository = UserRepository(session)

    existing = await repository.get(user_id)
    if existing is not None:
        return _map_user_to_profile(existing)

    user = await repository.create_with_id(user_id, UserCreate())
    # TODO: utilize payload.starter_card once starter deck logic is defined.
    return _map_user_to_profile(user)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserProfileResponse:
    """Return the current authenticated user profile."""

    return _map_user_to_profile(current_user)


def _map_user_to_profile(user: UserRead) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        debet_money=0,
        capital=0,
        energy=user.energy,
        experience=user.experience,
    )
