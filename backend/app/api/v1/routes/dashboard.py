from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_repositories
from app.models.domain import User
from app.repositories.factory import Repositories
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("")
async def dashboard(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)) -> dict:
    return await DashboardService(repos).stats(str(user.id))
