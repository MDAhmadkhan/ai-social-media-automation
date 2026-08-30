from datetime import UTC, datetime

from croniter import croniter

from app.models.enums import PostStatus, ScheduleMode
from app.repositories.factory import Repositories


class SchedulerService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    async def schedule(
        self,
        owner_id: str,
        generated_post_id: str,
        social_account_id: str,
        mode: ScheduleMode,
        scheduled_for: datetime | None,
        recurring_cron: str | None,
        approval_required: bool,
    ):
        post = await self.repos.generated_posts.get(generated_post_id)
        account = await self.repos.social_accounts.get(social_account_id)
        if not post or post.owner_id != owner_id:
            raise ValueError("Generated post was not found")
        if not account or account.owner_id != owner_id:
            raise ValueError("Social account was not found")
        if account.platform != post.platform:
            raise ValueError("Choose an account that matches the generated post platform")
        status = PostStatus.pending_approval if approval_required or mode == ScheduleMode.approval else PostStatus.scheduled
        if mode == ScheduleMode.immediate:
            scheduled_for = datetime.now(UTC)
        if mode == ScheduleMode.recurring:
            if not recurring_cron or not croniter.is_valid(recurring_cron):
                raise ValueError("A valid recurring cron expression is required")
            scheduled_for = croniter(recurring_cron, datetime.now(UTC)).get_next(datetime)
        if mode == ScheduleMode.draft:
            status = PostStatus.draft
        return await self.repos.scheduled_posts.create(
            {
                "owner_id": owner_id,
                "generated_post_id": generated_post_id,
                "social_account_id": social_account_id,
                "platform": post.platform,
                "mode": mode,
                "scheduled_for": scheduled_for,
                "recurring_cron": recurring_cron,
                "approval_required": approval_required,
                "status": status,
            }
        )

    async def due_posts(self, limit: int = 100):
        return await self.repos.scheduled_posts.list(
            {"status": PostStatus.scheduled, "scheduled_for": {"$lte": datetime.now(UTC)}},
            limit=limit,
            sort=[("scheduled_for", 1)],
        )
