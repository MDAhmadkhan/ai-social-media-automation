from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.core.deps import get_current_user, get_repositories, require_roles
from app.models.domain import User
from app.models.enums import PostStatus, ScheduleMode, UserRole
from app.repositories.factory import Repositories
from app.schemas.common import ScheduleRequest, StatusUpdate
from app.services.scheduler_service import SchedulerService
from app.services.social.publisher import PublisherService
from app.tasks.automation import publish_due_posts

router = APIRouter()
settings = get_settings()


@router.post("")
async def schedule_post(
    payload: ScheduleRequest,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.editor)),
    repos: Repositories = Depends(get_repositories),
):
    try:
        scheduled = await SchedulerService(repos).schedule(
            str(user.id),
            payload.generated_post_id,
            payload.social_account_id,
            payload.mode,
            payload.scheduled_for,
            payload.recurring_cron,
            payload.approval_required,
        )
        if payload.mode == ScheduleMode.immediate and settings.mongodb_uri.startswith("mongomock://"):
            try:
                await PublisherService(repos).publish_scheduled_post(str(scheduled.id))
            except Exception:
                pass
            return await repos.scheduled_posts.get(str(scheduled.id))
        return scheduled
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
async def list_schedules(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    return await repos.scheduled_posts.list({"owner_id": str(user.id)}, sort=[("scheduled_for", 1)])


@router.patch("/{schedule_id}/status")
async def update_status(
    schedule_id: str,
    payload: StatusUpdate,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    repos: Repositories = Depends(get_repositories),
):
    item = await repos.scheduled_posts.get(schedule_id)
    if not item or item.owner_id != str(user.id):
        raise HTTPException(status_code=404, detail="Schedule not found")
    updated = await repos.scheduled_posts.update(schedule_id, {"status": payload.status})
    if payload.status == PostStatus.scheduled:
        if settings.mongodb_uri.startswith("mongomock://"):
            try:
                await PublisherService(repos).publish_scheduled_post(schedule_id)
            except Exception:
                pass
        else:
            publish_due_posts.delay()
    return updated
