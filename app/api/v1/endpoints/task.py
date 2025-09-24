from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas import TaskListResponse, TaskRewardRequest

router = APIRouter(prefix="/task", tags=["task"])


@router.get("/list", response_model=TaskListResponse, status_code=status.HTTP_200_OK)
async def list_tasks(
    _current_user: CurrentUser,
    _session: SessionDep,
) -> TaskListResponse:
    """Return the list of tasks paired with user progress."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/get_reward", status_code=status.HTTP_202_ACCEPTED)
async def get_task_reward(
    payload: TaskRewardRequest,
    _current_user: CurrentUser,
    _session: SessionDep,
) -> None:
    """Mark the task reward as claimed for the provided progress entry."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
