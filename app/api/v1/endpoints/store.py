from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import StoreBuyRequest, StoreListResponse

router = APIRouter(prefix="/store", tags=["store"])


@router.get("/list", response_model=StoreListResponse, status_code=status.HTTP_200_OK)
async def list_store_items(
    _current_user: CurrentUser,
    _session: SessionDep,
) -> StoreListResponse:
    """Retrieve the items available in the store."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/buy", status_code=status.HTTP_202_ACCEPTED)
async def buy_store_item(
    payload: StoreBuyRequest,
    _current_user: CurrentUser,
    _session: SessionDep,
) -> None:
    """Purchase an item from the store."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
