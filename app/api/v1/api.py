from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.api.v1.endpoints import analytics, health, savings, store, task, user, work

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(user.router)
api_router.include_router(work.router, dependencies=[Depends(get_current_user)])
api_router.include_router(store.router, dependencies=[Depends(get_current_user)])
api_router.include_router(task.router, dependencies=[Depends(get_current_user)])
api_router.include_router(analytics.router, dependencies=[Depends(get_current_user)])
api_router.include_router(savings.router, dependencies=[Depends(get_current_user)])
