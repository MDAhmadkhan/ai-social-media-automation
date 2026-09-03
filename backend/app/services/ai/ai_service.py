from typing import Any
import re
import hashlib
from urllib.parse import quote

from app.core.config import get_settings
from app.models.domain import ContentItem, GeneratedPost
from app.models.enums import Platform
from app.repositories.factory import Repositories
from app.services.ai.image_service import ImageService
from app.services.ai.providers import get_ai_provider
from app.services.ai.social_card import SocialCardGenerator


class AIService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos
        self.settings = get_settings()

    async def generate_for_content(self, owner_id: str, content_item_id: str, platforms: list[Platform], generate_images: bool) -> list[GeneratedPost]:
        content = await self.repos.content_items.get(content_item_id)
        if not content or content.owner_id != owner_id:
            raise ValueError("Content item was not found")
        brand = await self.repos.brand_settings.find_one({"owner_id": owner_id})
        if not brand:
            raise ValueError("Brand settings were not found")
        try:
            bundle = await get_ai_provider().generate_social_bundle(content, brand, platforms)
        except RuntimeError:
            if self.settings.environment != "local":
                raise
            bundle = self._local_social_bundle(content, brand, platforms)
        await self.repos.content_items.update(
            content_item_id,
            {
                "seo_summary": bundle.get("seo_summary"),
                "short_summary": bundle.get("short_summary"),
                "long_summary": bundle.get("long_summary"),
                "callout_points": bundle.get("callout_points", []),
            },
        )
        image_urls = await self._image_urls(content, bundle, generate_images, brand.logo_url)
        posts: list[GeneratedPost] = []
        for platform in platforms:
            payload: dict[str, Any] = bundle.get("posts", {}).get(platform.value, {})
            hashtags = self._normalize_hashtags(payload.get("hashtags", []), brand.hashtag_count)
            post = await self.repos.generated_posts.create(
                {
                    "owner_id": owner_id,
                    "content_item_id": content_item_id,
                    "platform": platform,
                    "text": payload.get("text", ""),
                    "hashtags": hashtags,
                    "cta": payload.get("cta", brand.default_cta),
                    "image_urls": image_urls,
                    "status": "draft",
                }
            )
            posts.append(post)
        return posts

    async def generate_from_prompt(
        self,
        owner_id: str,
        prompt: str,
        title: str | None,
        platforms: list[Platform],
        generate_images: bool,
        image_prompt: str | None,
    ) -> list[GeneratedPost]:
        prompt_title = (title or self._sentence(prompt, 90)).strip()
        if len(prompt_title) < 3:
            raise ValueError("Write a post title so the AI can create useful content.")
        clean_prompt = " ".join((prompt or f"Create a professional Facebook post about: {prompt_title}").split())
        slug = quote(re.sub(r"[^a-z0-9]+", "-", prompt_title.lower()).strip("-") or "prompt-post")
        source_hash = hashlib.sha256(clean_prompt.encode()).hexdigest()
        content = await self.repos.content_items.create(
            {
                "owner_id": owner_id,
                "website_id": "prompt",
                "canonical_url": f"https://local.prompt/{slug}",
                "title": prompt_title,
                "meta_description": self._sentence(clean_prompt, 180),
                "keywords": [],
                "raw_text": clean_prompt,
                "source_hash": source_hash,
                "generated_assets": {
                    "source": "prompt",
                    "image_prompt": image_prompt or f"Professional social media image for: {prompt_title}",
                },
            }
        )
        return await self.generate_for_content(owner_id, str(content.id), platforms, generate_images)

    async def generate_topic_pack(self, owner_id: str, topic: str, platforms: list[Platform], count: int = 10) -> list[GeneratedPost]:
        clean_topic = " ".join(topic.split())
        if len(clean_topic) < 3:
            raise ValueError("Write a niche or post topic first.")
        allowed_platforms = [platform for platform in platforms if platform in {Platform.facebook, Platform.instagram}]
        if not allowed_platforms:
            raise ValueError("Choose Facebook, Instagram, or both.")
        brand = await self.repos.brand_settings.find_one({"owner_id": owner_id})
        if not brand:
            raise ValueError("Brand settings were not found")
        ideas = self._topic_post_ideas(clean_topic, min(max(count, 1), 10))
        posts: list[GeneratedPost] = []
        for index, idea in enumerate(ideas, start=1):
            slug = quote(re.sub(r"[^a-z0-9]+", "-", f"{clean_topic}-{index}".lower()).strip("-") or f"topic-post-{index}")
            raw_text = f"{idea['hook']} {idea['body']} {idea['cta']}"
            content = await self.repos.content_items.create(
                {
                    "owner_id": owner_id,
                    "website_id": "topic-pack",
                    "canonical_url": f"https://local.prompt/{slug}",
                    "title": idea["title"],
                    "meta_description": self._sentence(raw_text, 180),
                    "keywords": self._topic_keywords(clean_topic),
                    "raw_text": raw_text,
                    "source_hash": hashlib.sha256(f"{clean_topic}:{index}:{raw_text}".encode()).hexdigest(),
                    "generated_assets": {"source": "topic-pack"},
                }
            )
            for platform in allowed_platforms:
                posts.append(
                    await self.repos.generated_posts.create(
                        {
                            "owner_id": owner_id,
                            "content_item_id": str(content.id),
                            "platform": platform,
                            "text": self._topic_post_text(platform, idea, clean_topic),
                            "hashtags": self._topic_hashtags(platform, clean_topic, brand.hashtag_count),
                            "cta": idea["cta"],
                            "image_urls": [],
                            "status": "draft",
                        }
                    )
                )
        return posts

    async def _generate_images(self, content: ContentItem, bundle: dict[str, Any]) -> list[str]:
        image_service = ImageService()
        prompts = [
            ("featured", f"Editorial featured image for: {content.title}. Professional SaaS social media style."),
            ("quote", f"Quote card visual using this quote concept: {bundle.get('quote_card_text', content.title)}"),
        ]
        return [await image_service.generate(prompt, kind) for kind, prompt in prompts]

    async def _image_urls(self, content: ContentItem, bundle: dict[str, Any], generate_images: bool, logo_url: str | None) -> list[str]:
        if generate_images:
            return await self._generate_images(content, bundle)
        if content.generated_assets.get("source") == "prompt":
            return []
        generator = SocialCardGenerator()
        existing_card = content.generated_assets.get("social_card_url")
        existing_version = content.generated_assets.get("social_card_version")
        existing_logo_url = content.generated_assets.get("social_card_logo_url")
        if (
            isinstance(existing_card, str)
            and existing_card.startswith(("http://", "https://"))
            and existing_version == generator.version
            and existing_logo_url == logo_url
        ):
            return [existing_card]
        card_url = generator.generate(content, bundle.get("short_summary"), logo_url)
        await self.repos.content_items.update(
            str(content.id),
            {
                "generated_assets": {
                    **content.generated_assets,
                    "social_card_url": card_url,
                    "social_card_version": generator.version,
                    "social_card_logo_url": logo_url,
                }
            },
        )
        return [card_url]

    def _existing_image_urls(self, content: ContentItem) -> list[str]:
        image_url = content.generated_assets.get("featured_image_url")
        return [image_url] if isinstance(image_url, str) and image_url.startswith(("http://", "https://")) else []

    def _local_social_bundle(self, content: ContentItem, brand: Any, platforms: list[Platform]) -> dict[str, Any]:
        summary = self._sentence(content.meta_description or content.raw_text or content.title, 180)
        tool_name = content.title.split("|")[0].replace("Online", "").strip()
        posts = {}
        for platform in platforms:
            posts[platform.value] = {
                "text": (
                    f"{tool_name} is ready on I Love Tool XYZ.\n\n"
                    f"{summary}\n\n"
                    "Use it when you need a quick browser-based workflow and review the result before publishing or sharing."
                ),
                "hashtags": ["I Love Tool XYZ", "Free Tools", "Online Tools", platform.value.title()],
                "cta": brand.default_cta,
            }
        return {
            "seo_summary": summary,
            "short_summary": summary,
            "long_summary": self._sentence(content.raw_text or summary, 500),
            "callout_points": ["Free browser-based utility", "Quick workflow", "Review before use"],
            "carousel_text": [tool_name, summary, brand.default_cta],
            "quote_card_text": f"Try {tool_name} online",
            "posts": posts,
        }

    def _topic_post_ideas(self, topic: str, count: int) -> list[dict[str, str]]:
        angles = [
            ("Problem", "Most people struggle with {topic} because they try to do everything at once.", "Start with one small step today."),
            ("Quick Tip", "Here is a simple way to improve your {topic} results without overcomplicating the process.", "Save this for later."),
            ("Mistake", "A common {topic} mistake is focusing on speed before clarity.", "Fix this before your next post."),
            ("Checklist", "Before you publish anything about {topic}, check your headline, message, offer, and next step.", "Use this as your quick checklist."),
            ("Story", "Every strong {topic} result starts with understanding what your audience actually needs.", "Share this with someone building the same thing."),
            ("Myth", "You do not need a huge budget to make progress with {topic}; you need consistency and useful content.", "Try this approach this week."),
            ("How To", "Break {topic} into small actions: plan the idea, write the message, add proof, then publish.", "Follow for more practical tips."),
            ("Benefits", "Good {topic} content builds trust, answers questions, and helps people take action faster.", "DM us if you want help getting started."),
            ("Comparison", "Random posting creates noise. Planned {topic} content creates momentum.", "Choose one clear goal for your next post."),
            ("Reminder", "Your audience does not need perfect content about {topic}; they need helpful content they can use.", "Post something useful today."),
        ]
        return [
            {
                "title": f"{label}: {topic}",
                "hook": label,
                "body": body.format(topic=topic),
                "cta": cta,
            }
            for label, body, cta in angles[:count]
        ]

    def _topic_post_text(self, platform: Platform, idea: dict[str, str], topic: str) -> str:
        if platform == Platform.instagram:
            return (
                f"{idea['hook']} for {topic}\n\n"
                f"{idea['body']}\n\n"
                f"{idea['cta']}"
            )
        return (
            f"{idea['hook']}: {topic}\n\n"
            f"{idea['body']}\n\n"
            f"{idea['cta']}"
        )

    def _topic_keywords(self, topic: str) -> list[str]:
        words = [word.lower() for word in re.findall(r"[A-Za-z0-9]+", topic) if len(word) > 2]
        return list(dict.fromkeys(words))[:8]

    def _topic_hashtags(self, platform: Platform, topic: str, limit: int) -> list[str]:
        base = self._topic_keywords(topic)
        generic = ["SocialMedia", "ContentMarketing", "DigitalMarketing", "SmallBusiness", "GrowthTips"]
        if platform == Platform.instagram:
            generic = ["InstagramTips", "ReelsIdeas", "ContentCreator", "InstaGrowth", "SocialMediaTips"]
        tags = [*base, *generic]
        return self._normalize_hashtags(tags, max(6, min(limit or 8, 12)))

    def _sentence(self, text: str, limit: int) -> str:
        clean = " ".join(text.split())
        if len(clean) <= limit:
            return clean
        return clean[:limit].rsplit(" ", 1)[0].rstrip(".,;:") + "."

    def _normalize_hashtags(self, hashtags: Any, limit: int) -> list[str]:
        if not isinstance(hashtags, list):
            hashtags = []
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in hashtags:
            text = re.sub(r"[^A-Za-z0-9_]", "", str(item).strip().lstrip("#"))
            if not text:
                continue
            tag = "#" + text[:40]
            key = tag.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(tag)
            if len(cleaned) >= max(0, limit):
                break
        return cleaned
