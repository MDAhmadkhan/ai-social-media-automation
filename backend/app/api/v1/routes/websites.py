from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.config import get_settings
from app.core.deps import get_current_user, get_repositories, require_roles
from app.models.domain import User
from app.models.enums import UserRole
from app.repositories.factory import Repositories
from app.schemas.common import ApiMessage, WebhookContent, WebsiteCreate
from app.services.content_service import ContentService
from app.tasks.automation import scan_website

router = APIRouter()
settings = get_settings()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_website(
    payload: WebsiteCreate,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    repos: Repositories = Depends(get_repositories),
):
    owner_id = str(user.id)
    url = str(payload.url)
    existing = await repos.websites.find_one({"owner_id": owner_id, "url": url})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This website is already connected.")
    try:
        return await repos.websites.create({**payload.model_dump(), "owner_id": owner_id})
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This website is already connected.") from exc


@router.get("")
async def list_websites(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    return await repos.websites.list({"owner_id": str(user.id)}, sort=[("created_at", -1)])


@router.post("/{website_id}/scan", response_model=ApiMessage)
async def scan(website_id: str, user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    website = await repos.websites.get(website_id)
    if not website or website.owner_id != str(user.id):
        raise HTTPException(status_code=404, detail="Website not found")
    if settings.mongodb_uri.startswith("mongomock://"):
        created = await ContentService(repos).detect_new_content(website)
        return ApiMessage(message=f"Website scan completed. New content: {len(created)}")
    scan_website.delay(website_id)
    return ApiMessage(message="Website scan queued")


@router.post("/{website_id}/webhook")
async def webhook(website_id: str, payload: WebhookContent, repos: Repositories = Depends(get_repositories)):
    website = await repos.websites.get(website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return await ContentService(repos).ingest_url(website.owner_id, website_id, str(payload.url))
