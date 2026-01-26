"""API v1 router combining all endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    dashboard,
    heritage,
    media,
    news,
    timeline,
    uploads,
    users,
    visit_info,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(heritage.router, prefix="/heritage", tags=["heritage"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(visit_info.router, prefix="/visit-info", tags=["visit-info"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
