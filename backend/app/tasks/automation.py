import asyncio
from datetime import UTC, datetime

from bson import ObjectId

from app.core.celery_app import celery_app
from app.core.database import get_database
from app.models.domain import Website
from app.models.enums import PostStatus
from app.repositories.factory import Repositories
from app.services.content_service import ContentService
from app.services.scheduler_service import SchedulerService
from app.services.social.publisher import PublisherService


def run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="automation.scan_website")
def scan_website(website_id: str) -> int:
    async def _run() -> int:
        repos = Repositories(get_database())
        website_doc = await get_database().websites.find_one({"_id": ObjectId(website_id)})
        if not website_doc:
            return 0
        created = await ContentService(repos).detect_new_content(Website.model_validate(website_doc))
        return len(created)

    return run_async(_run())


@celery_app.task(name="automation.publish_due_posts")
def publish_due_posts() -> int:
    async def _run() -> int:
        repos = Repositories(get_database())
        due = await SchedulerService(repos).due_posts()
        published = 0
        for item in due:
            try:
                await PublisherService(repos).publish_scheduled_post(str(item.id))
                published += 1
            except Exception:
                continue
            if item.recurring_cron:
                from croniter import croniter

                next_run = croniter(item.recurring_cron, datetime.now(UTC)).get_next(datetime)
                await repos.scheduled_posts.create(
                    {
                        "owner_id": item.owner_id,
                        "generated_post_id": item.generated_post_id,
                        "social_account_id": item.social_account_id,
                        "platform": item.platform,
                        "mode": item.mode,
                        "scheduled_for": next_run,
                        "recurring_cron": item.recurring_cron,
                        "approval_required": item.approval_required,
                        "status": PostStatus.scheduled,
                    }
                )
        return published

    return run_async(_run())


@celery_app.task(name="automation.scan_all_websites")
def scan_all_websites() -> int:
    async def _run() -> int:
        db = get_database()
        count = 0
        async for doc in db.websites.find({"is_active": True}):
            scan_website.delay(str(doc["_id"]))
            count += 1
        return count

    return run_async(_run())
