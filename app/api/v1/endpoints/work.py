from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import (
    WorkListResponse,
    WorkStartResponse,
    WorkStopRequest,
    WorkStopResponse,
)

router = APIRouter(prefix="/work", tags=["work"])


@router.get("/list", response_model=WorkListResponse, status_code=status.HTTP_200_OK)
async def list_work(
    _current_user: CurrentUser,
    _session: SessionDep,
) -> WorkListResponse:
    """Retrieve the list of available work activities."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post(
    "/start", response_model=WorkStartResponse, status_code=status.HTTP_201_CREATED
)
async def start_work(
    _current_user: CurrentUser,
    _session: SessionDep,
) -> WorkStartResponse:
    """Start a work session for the current user."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/stop", response_model=WorkStopResponse, status_code=status.HTTP_200_OK)
async def stop_work(
    payload: WorkStopRequest,
    _current_user: CurrentUser,
    _session: SessionDep,
) -> WorkStopResponse:
    """Complete a work session and grant rewards."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
