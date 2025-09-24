from fastapi import APIRouter, HTTPException, Header, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import UserCreateRequest, UserProfileResponse

router = APIRouter(prefix="/user", tags=["user"])


@router.post(
    "", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    payload: UserCreateRequest,
    _session: SessionDep,
    user_agent: str | None = Header(default=None, alias="User-Agent"),
) -> UserProfileResponse:
    """Register a user with the given starter card."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    _current_user: CurrentUser,
    _session: SessionDep,
) -> UserProfileResponse:
    """Return the current authenticated user profile."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
