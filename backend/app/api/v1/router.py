from fastapi import APIRouter

from app.api.v1.routes import ai, analytics, auth, content, dashboard, logs, schedules, settings, social_accounts, websites

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(websites.router, prefix="/websites", tags=["websites"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(social_accounts.router, prefix="/social-accounts", tags=["social accounts"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
