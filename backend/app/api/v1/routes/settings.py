from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import get_current_user, get_repositories, require_roles
from app.models.domain import User
from app.models.enums import UserRole
from app.repositories.factory import Repositories
from app.schemas.common import BrandSettingsUpdate
from app.services.storage.adapters import get_storage_adapter

router = APIRouter()

MAX_LOGO_BYTES = 3 * 1024 * 1024
ALLOWED_LOGO_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


@router.get("/brand")
async def get_brand_settings(user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)):
    return await repos.brand_settings.find_one({"owner_id": str(user.id)})


@router.patch("/brand")
async def update_brand_settings(
    payload: BrandSettingsUpdate,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    repos: Repositories = Depends(get_repositories),
):
    current = await repos.brand_settings.find_one({"owner_id": str(user.id)})
    return await repos.brand_settings.update(str(current.id), payload.model_dump(exclude_unset=True)) if current else None


@router.post("/brand/logo")
async def upload_brand_logo(
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    repos: Repositories = Depends(get_repositories),
):
    if file.content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(status_code=400, detail="Logo must be PNG, JPG, or WebP")
    data = await file.read()
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Logo must be smaller than 3 MB")
    path = get_storage_adapter().save_bytes(data, file.content_type, ALLOWED_LOGO_TYPES[file.content_type])
    current = await repos.brand_settings.find_one({"owner_id": str(user.id)})
    if not current:
        raise HTTPException(status_code=404, detail="Brand settings were not found")
    return await repos.brand_settings.update(str(current.id), {"logo_url": path})
