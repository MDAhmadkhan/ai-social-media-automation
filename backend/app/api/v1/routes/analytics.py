from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_repositories
from app.models.domain import User
from app.repositories.factory import Repositories

router = APIRouter()


@router.get("")
async def analytics(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    records = await repos.analytics.list({"owner_id": str(user.id)}, limit=500, sort=[("created_at", -1)])
    by_platform: dict[str, dict[str, int | float]] = {}
    for item in records:
        metrics = by_platform.setdefault(item.platform, {"clicks": 0, "likes": 0, "comments": 0, "shares": 0, "reach": 0, "impressions": 0, "ctr": 0})
        for key in ("clicks", "likes", "comments", "shares", "reach", "impressions"):
            metrics[key] += getattr(item, key)
    for metrics in by_platform.values():
        metrics["ctr"] = round((metrics["clicks"] / metrics["impressions"]) * 100, 2) if metrics["impressions"] else 0
    return {"records": records, "platform_comparison": by_platform}
