from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_repositories, require_roles
from app.core.security import encrypt_secret
from app.models.domain import User
from app.models.enums import UserRole
from app.repositories.factory import Repositories
from app.schemas.common import SocialAccountCreate

router = APIRouter()


@router.post("")
async def connect_account(
    payload: SocialAccountCreate,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    repos: Repositories = Depends(get_repositories),
):
    return await repos.social_accounts.create(
        {
            "owner_id": str(user.id),
            "platform": payload.platform,
            "display_name": payload.display_name,
            "external_id": payload.external_id,
            "encrypted_access_token": encrypt_secret(payload.access_token),
            "encrypted_refresh_token": encrypt_secret(payload.refresh_token) if payload.refresh_token else None,
            "metadata": payload.metadata,
        }
    )


@router.get("")
async def list_accounts(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    return await repos.social_accounts.list({"owner_id": str(user.id)}, sort=[("created_at", -1)])
