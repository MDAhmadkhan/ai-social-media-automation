from datetime import UTC, datetime

import structlog
from pymongo.errors import DuplicateKeyError

from app.models.domain import ContentItem, Website
from app.repositories.factory import Repositories
from app.services.web_reader import WebReader

logger = structlog.get_logger()


class ContentService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos
        self.reader = WebReader()

    async def detect_new_content(self, website: Website) -> list[ContentItem]:
        urls = await self.reader.discover_urls(str(website.url), website.type)
        created: list[ContentItem] = []
        for url in urls[:25]:
            page = await self.reader.read(url)
            existing = await self.repos.content_items.find_one({"website_id": str(website.id), "canonical_url": page.url})
            if existing and existing.source_hash == page.source_hash:
                continue
            try:
                item = await self.repos.content_items.create(
                    {
                        "owner_id": website.owner_id,
                        "website_id": str(website.id),
                        "canonical_url": page.url,
                        "title": page.title,
                        "meta_description": page.description,
                        "keywords": page.keywords,
                        "raw_text": page.text,
                        "source_hash": page.source_hash,
                        "generated_assets": {"featured_image_url": page.image_url} if page.image_url else {},
                    }
                )
                created.append(item)
            except DuplicateKeyError:
                logger.info("content_duplicate_ignored", url=page.url)
        await self.repos.websites.update(str(website.id), {"last_checked_at": datetime.now(UTC)})
        return created

    async def ingest_url(self, owner_id: str, website_id: str, url: str) -> ContentItem:
        website = await self.repos.websites.get(website_id)
        if not website or website.owner_id != owner_id:
            raise ValueError("Website was not found")
        page = await self.reader.read(url)
        existing = await self.repos.content_items.find_one({"website_id": website_id, "canonical_url": page.url})
        if existing:
            return existing
        return await self.repos.content_items.create(
            {
                "owner_id": owner_id,
                "website_id": website_id,
                "canonical_url": page.url,
                "title": page.title,
                "meta_description": page.description,
                "keywords": page.keywords,
                "raw_text": page.text,
                "source_hash": page.source_hash,
                "generated_assets": {"featured_image_url": page.image_url} if page.image_url else {},
            }
        )
