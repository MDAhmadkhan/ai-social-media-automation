from datetime import datetime
from typing import Any

from pydantic import EmailStr, Field, HttpUrl

from app.models.base import MongoModel
from app.models.enums import Language, Platform, PostStatus, ScheduleMode, Tone, UserRole, WebsiteType


class User(MongoModel):
    email: EmailStr
    full_name: str
    password_hash: str | None = None
    google_sub: str | None = None
    role: UserRole = UserRole.admin
    is_active: bool = True


class BrandSettings(MongoModel):
    owner_id: str
    brand_voice: str = "Clear, useful, trustworthy, and concise."
    logo_url: str | None = None
    language: Language = Language.en
    tone: Tone = Tone.professional
    emoji_level: int = Field(default=1, ge=0, le=3)
    hashtag_count: int = Field(default=6, ge=0, le=20)
    default_cta: str = "Read the full article"
    timezone: str = "UTC"
    posting_schedule: dict[str, list[str]] = Field(default_factory=dict)


class Website(MongoModel):
    owner_id: str
    name: str
    url: HttpUrl
    type: WebsiteType
    is_active: bool = True
    last_checked_at: datetime | None = None
    webhook_secret: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ContentItem(MongoModel):
    owner_id: str
    website_id: str
    canonical_url: HttpUrl
    title: str
    meta_description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    raw_text: str
    seo_summary: str | None = None
    short_summary: str | None = None
    long_summary: str | None = None
    callout_points: list[str] = Field(default_factory=list)
    source_hash: str
    generated_assets: dict[str, Any] = Field(default_factory=dict)


class SocialAccount(MongoModel):
    owner_id: str
    platform: Platform
    display_name: str
    external_id: str
    encrypted_access_token: str
    encrypted_refresh_token: str | None = None
    token_expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class GeneratedPost(MongoModel):
    owner_id: str
    content_item_id: str
    platform: Platform
    text: str
    hashtags: list[str] = Field(default_factory=list)
    cta: str
    image_urls: list[str] = Field(default_factory=list)
    status: PostStatus = PostStatus.draft


class ScheduledPost(MongoModel):
    owner_id: str
    generated_post_id: str
    social_account_id: str
    platform: Platform
    mode: ScheduleMode
    scheduled_for: datetime | None = None
    recurring_cron: str | None = None
    status: PostStatus = PostStatus.scheduled
    approval_required: bool = False
    publish_result: dict[str, Any] = Field(default_factory=dict)
    failure_reason: str | None = None


class AnalyticsRecord(MongoModel):
    owner_id: str
    platform: Platform
    scheduled_post_id: str
    clicks: int = 0
    shares: int = 0
    likes: int = 0
    comments: int = 0
    reach: int = 0
    impressions: int = 0
    ctr: float = 0


class AuditLog(MongoModel):
    actor_id: str | None = None
    action: str
    entity: str
    entity_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
