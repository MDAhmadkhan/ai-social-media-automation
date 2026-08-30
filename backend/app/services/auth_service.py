from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.domain import BrandSettings, User
from app.repositories.factory import Repositories
from app.schemas.common import TokenPair

settings = get_settings()


class AuthService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    async def register(self, email: str, full_name: str, password: str, role: str) -> User:
        existing = await self.repos.users.find_one({"email": email.lower()})
        if existing:
            raise ValueError("Email is already registered")
        user = await self.repos.users.create(
            {"email": email.lower(), "full_name": full_name, "password_hash": hash_password(password), "role": role}
        )
        await self.repos.brand_settings.create(BrandSettings(owner_id=str(user.id)).model_dump(by_alias=True, exclude={"id"}))
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.repos.users.find_one({"email": email.lower()})
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        return self._tokens(user)

    async def google_login(self, google_id_token: str) -> TokenPair:
        if not settings.google_client_id:
            raise ValueError("Google login is not configured")
        info = id_token.verify_oauth2_token(google_id_token, requests.Request(), settings.google_client_id)
        email = info.get("email")
        if not email:
            raise ValueError("Google token did not include an email")
        user = await self.repos.users.find_one({"email": email.lower()})
        if not user:
            user = await self.repos.users.create(
                {"email": email.lower(), "full_name": info.get("name", email), "google_sub": info["sub"], "role": "admin"}
            )
            await self.repos.brand_settings.create(BrandSettings(owner_id=str(user.id)).model_dump(by_alias=True, exclude={"id"}))
        return self._tokens(user)

    def _tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(str(user.id), {"role": user.role, "email": user.email}),
            refresh_token=create_refresh_token(str(user.id)),
        )
