from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.domain import (
    AnalyticsRecord,
    AuditLog,
    BrandSettings,
    ContentItem,
    GeneratedPost,
    ScheduledPost,
    SocialAccount,
    User,
    Website,
)
from app.repositories.base import MongoRepository


class Repositories:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.users = MongoRepository(db, "users", User)
        self.brand_settings = MongoRepository(db, "brand_settings", BrandSettings)
        self.websites = MongoRepository(db, "websites", Website)
        self.content_items = MongoRepository(db, "content_items", ContentItem)
        self.social_accounts = MongoRepository(db, "social_accounts", SocialAccount)
        self.generated_posts = MongoRepository(db, "generated_posts", GeneratedPost)
        self.scheduled_posts = MongoRepository(db, "scheduled_posts", ScheduledPost)
        self.analytics = MongoRepository(db, "analytics", AnalyticsRecord)
        self.audit_logs = MongoRepository(db, "audit_logs", AuditLog)
