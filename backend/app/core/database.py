from collections.abc import AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from mongomock_motor import AsyncMongoMockClient

from app.core.config import get_settings

settings = get_settings()
if settings.mongodb_uri.startswith("mongomock://"):
    mongo_client = AsyncMongoMockClient()
else:
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri, uuidRepresentation="standard")


def get_database() -> AsyncIOMotorDatabase:
    return mongo_client[settings.mongodb_db]


async def database_dependency() -> AsyncIterator[AsyncIOMotorDatabase]:
    yield get_database()


async def ensure_indexes() -> None:
    db = get_database()
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.websites.create_index([("owner_id", 1), ("url", 1)], unique=True)
    await db.content_items.create_index([("website_id", 1), ("canonical_url", 1)], unique=True)
    await db.social_accounts.create_index([("owner_id", 1), ("platform", 1), ("external_id", 1)], unique=True)
    await db.scheduled_posts.create_index([("status", 1), ("scheduled_for", 1)])
    await db.analytics.create_index([("owner_id", 1), ("platform", 1), ("created_at", -1)])
    await db.audit_logs.create_index([("actor_id", 1), ("created_at", -1)])
