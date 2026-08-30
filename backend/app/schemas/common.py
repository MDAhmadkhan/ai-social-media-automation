from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl

from app.models.enums import Language, Platform, PostStatus, ScheduleMode, Tone, UserRole, WebsiteType


class ApiMessage(BaseModel):
    message: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.admin


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleLogin(BaseModel):
    id_token: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class WebsiteCreate(BaseModel):
    name: str
    url: HttpUrl
    type: WebsiteType
    options: dict[str, Any] = {}


class WebsiteRead(WebsiteCreate):
    id: str | None = None
    is_active: bool
    last_checked_at: datetime | None = None


class BrandSettingsUpdate(BaseModel):
    brand_voice: str | None = None
    logo_url: str | None = None
    language: Language | None = None
    tone: Tone | None = None
    emoji_level: int | None = None
    hashtag_count: int | None = None
    default_cta: str | None = None
    timezone: str | None = None
    posting_schedule: dict[str, list[str]] | None = None


class SocialAccountCreate(BaseModel):
    platform: Platform
    display_name: str
    external_id: str
    access_token: str
    refresh_token: str | None = None
    metadata: dict[str, Any] = {}


class ContentRead(BaseModel):
    id: str | None = None
    website_id: str
    canonical_url: HttpUrl
    title: str
    meta_description: str | None = None
    keywords: list[str]
    short_summary: str | None = None
    long_summary: str | None = None
    callout_points: list[str]


class GenerateRequest(BaseModel):
    content_item_id: str
    platforms: list[Platform]
    generate_images: bool = True


class PromptGenerateRequest(BaseModel):
    prompt: str
    title: str | None = None
    platforms: list[Platform]
    generate_images: bool = False
    image_prompt: str | None = None


class BulkGenerateRequest(BaseModel):
    platforms: list[Platform]
    generate_images: bool = False
    limit: int = 50


class ScheduleRequest(BaseModel):
    generated_post_id: str
    social_account_id: str
    mode: ScheduleMode
    scheduled_for: datetime | None = None
    recurring_cron: str | None = None
    approval_required: bool = False


class StatusUpdate(BaseModel):
    status: PostStatus


class WebhookContent(BaseModel):
    url: HttpUrl
