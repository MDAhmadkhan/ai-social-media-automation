from datetime import UTC, datetime

from app.core.security import decrypt_secret
from app.models.enums import PostStatus
from app.repositories.factory import Repositories
from app.services.social.adapters import get_social_adapter


class PublisherService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    async def publish_scheduled_post(self, scheduled_post_id: str) -> None:
        scheduled = await self.repos.scheduled_posts.get(scheduled_post_id)
        if not scheduled or scheduled.status not in {PostStatus.scheduled, PostStatus.publishing}:
            return
        await self.repos.scheduled_posts.update(str(scheduled.id), {"status": PostStatus.publishing})
        post = await self.repos.generated_posts.get(scheduled.generated_post_id)
        account = await self.repos.social_accounts.get(scheduled.social_account_id)
        if not post or not account:
            await self.repos.scheduled_posts.update(str(scheduled.id), {"status": PostStatus.failed, "failure_reason": "Post or account missing"})
            return
        try:
            result = await get_social_adapter(scheduled.platform).publish(account, post, decrypt_secret(account.encrypted_access_token))
            await self.repos.scheduled_posts.update(str(scheduled.id), {"status": PostStatus.published, "publish_result": result})
            await self.repos.generated_posts.update(str(post.id), {"status": PostStatus.published})
            await self.repos.analytics.create({"owner_id": scheduled.owner_id, "platform": scheduled.platform, "scheduled_post_id": str(scheduled.id)})
        except Exception as exc:
            await self.repos.scheduled_posts.update(
                str(scheduled.id),
                {"status": PostStatus.failed, "failure_reason": str(exc), "updated_at": datetime.now(UTC)},
            )
            raise
