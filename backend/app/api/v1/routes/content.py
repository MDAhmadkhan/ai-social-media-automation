from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_repositories
from app.models.domain import User
from app.repositories.factory import Repositories

router = APIRouter()


@router.get("")
async def list_content(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    return await repos.content_items.list({"owner_id": str(user.id)}, limit=100, sort=[("created_at", -1)])


@router.get("/{content_id}")
async def get_content(content_id: str, user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    item = await repos.content_items.get(content_id)
    if not item or item.owner_id != str(user.id):
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Content not found")
    return item
