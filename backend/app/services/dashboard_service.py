from app.models.enums import PostStatus
from app.repositories.factory import Repositories


class DashboardService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    async def stats(self, owner_id: str) -> dict:
        counts = {
            "websites": await self.repos.websites.count({"owner_id": owner_id}),
            "connected_accounts": await self.repos.social_accounts.count({"owner_id": owner_id, "is_active": True}),
            "drafts": await self.repos.generated_posts.count({"owner_id": owner_id, "status": PostStatus.draft}),
            "scheduled": await self.repos.scheduled_posts.count({"owner_id": owner_id, "status": PostStatus.scheduled}),
            "published": await self.repos.scheduled_posts.count({"owner_id": owner_id, "status": PostStatus.published}),
            "failed": await self.repos.scheduled_posts.count({"owner_id": owner_id, "status": PostStatus.failed}),
        }
        analytics = await self.repos.analytics.list({"owner_id": owner_id}, limit=500)
        totals = {
            "clicks": sum(item.clicks for item in analytics),
            "shares": sum(item.shares for item in analytics),
            "likes": sum(item.likes for item in analytics),
            "comments": sum(item.comments for item in analytics),
            "reach": sum(item.reach for item in analytics),
            "impressions": sum(item.impressions for item in analytics),
        }
        totals["ctr"] = round((totals["clicks"] / totals["impressions"]) * 100, 2) if totals["impressions"] else 0
        return {"counts": counts, "analytics": totals, "ai_credits": {"used": 0, "remaining": "provider-managed"}}
