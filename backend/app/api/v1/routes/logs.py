from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_repositories, require_roles
from app.models.domain import User
from app.models.enums import UserRole
from app.repositories.factory import Repositories

router = APIRouter()


@router.get("")
async def logs(
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    repos: Repositories = Depends(get_repositories),
):
    return await repos.audit_logs.list({"actor_id": str(user.id)}, limit=200, sort=[("created_at", -1)])
