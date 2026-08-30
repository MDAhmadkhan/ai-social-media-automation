from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.database import database_dependency
from app.core.security import decode_token
from app.models.domain import BrandSettings, User
from app.models.enums import UserRole
from app.repositories.factory import Repositories

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_repositories(db: AsyncIOMotorDatabase = Depends(database_dependency)) -> Repositories:
    return Repositories(db)


async def get_current_user(token: str = Depends(oauth2_scheme), repos: Repositories = Depends(get_repositories)) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc
    user = await repos.users.get(payload["sub"])
    if not user and settings.mongodb_uri.startswith("mongomock://") and ObjectId.is_valid(payload["sub"]):
        user = await repos.users.create(
            {
                "_id": ObjectId(payload["sub"]),
                "email": payload.get("email", "local@example.com"),
                "full_name": payload.get("email", "Local User"),
                "role": payload.get("role", UserRole.admin),
                "is_active": True,
            }
        )
        existing_brand = await repos.brand_settings.find_one({"owner_id": str(user.id)})
        if not existing_brand:
            await repos.brand_settings.create(BrandSettings(owner_id=str(user.id)).model_dump(by_alias=True, exclude={"id"}))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency
