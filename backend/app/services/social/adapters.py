from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings
from app.models.domain import GeneratedPost, SocialAccount
from app.models.enums import Platform

settings = get_settings()


def _graph_error(response: httpx.Response) -> str:
    try:
        error = response.json().get("error", {})
        message = error.get("message") or response.text
        code = error.get("code")
        subcode = error.get("error_subcode")
        parts = [message]
        if code:
            parts.append(f"code={code}")
        if subcode:
            parts.append(f"subcode={subcode}")
        return "Facebook API error: " + " ".join(parts)
    except ValueError:
        return f"Facebook API error: {response.status_code} {response.text}"


class SocialAdapter(ABC):
    @abstractmethod
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        raise NotImplementedError


class FacebookAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        page_id = account.external_id
        caption = self._caption(post)
        endpoint = "photos" if post.image_urls else "feed"
        url = f"https://graph.facebook.com/{settings.facebook_graph_version}/{page_id}/{endpoint}"
        data = {"access_token": access_token}
        if post.image_urls:
            data.update({"caption": caption})
        else:
            data.update({"message": caption})
        async with httpx.AsyncClient(timeout=30) as client:
            local_file = self._local_storage_file(post.image_urls[0]) if post.image_urls else None
            if local_file:
                with local_file.open("rb") as image:
                    response = await client.post(url, data=data, files={"source": (local_file.name, image, "image/png")})
            else:
                if post.image_urls:
                    data["url"] = post.image_urls[0]
                response = await client.post(url, data=data)
            if response.status_code >= 400:
                raise RuntimeError(_graph_error(response))
            return response.json()

    def _caption(self, post: GeneratedPost) -> str:
        parts = [post.text.strip()]
        if post.cta:
            parts.append(post.cta.strip())
        if post.hashtags:
            parts.append(" ".join(post.hashtags))
        return "\n\n".join(part for part in parts if part)

    def _local_storage_file(self, image_url: str) -> Path | None:
        prefix = settings.public_base_url.rstrip("/") + "/storage/"
        if not image_url.startswith(prefix):
            return None
        filename = image_url.removeprefix(prefix)
        path = Path(settings.local_storage_path) / filename
        return path if path.is_file() else None


class InstagramAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        if not post.image_urls:
            raise ValueError("Instagram publishing requires at least one image URL")
        if post.image_urls[0].startswith(("http://localhost", "http://127.0.0.1")):
            raise ValueError("Instagram publishing requires a public HTTPS image URL. Configure public storage before publishing generated local images.")
        media_url = f"https://graph.facebook.com/{settings.facebook_graph_version}/{account.external_id}/media"
        publish_url = f"https://graph.facebook.com/{settings.facebook_graph_version}/{account.external_id}/media_publish"
        async with httpx.AsyncClient(timeout=60) as client:
            media = await client.post(media_url, data={"image_url": post.image_urls[0], "caption": post.text, "access_token": access_token})
            media.raise_for_status()
            creation_id = media.json()["id"]
            publish = await client.post(publish_url, data={"creation_id": creation_id, "access_token": access_token})
            publish.raise_for_status()
            return publish.json()


class LinkedInAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        payload = {
            "author": f"urn:li:organization:{account.external_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": post.text}, "shareMediaCategory": "NONE"}},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.linkedin_api_base}/ugcPosts",
                headers={"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0"},
                json=payload,
            )
            response.raise_for_status()
            return {"id": response.headers.get("x-restli-id")}


class TwitterAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.twitter_api_base}/tweets",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"text": post.text[:280]},
            )
            response.raise_for_status()
            return response.json()


class ThreadsAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            create = await client.post(
                f"{settings.threads_api_base}/{account.external_id}/threads",
                data={"media_type": "TEXT", "text": post.text, "access_token": access_token},
            )
            create.raise_for_status()
            publish = await client.post(
                f"{settings.threads_api_base}/{account.external_id}/threads_publish",
                data={"creation_id": create.json()["id"], "access_token": access_token},
            )
            publish.raise_for_status()
            return publish.json()


class PinterestAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        board_id = account.metadata.get("board_id")
        if not board_id or not post.image_urls:
            raise ValueError("Pinterest requires metadata.board_id and an image URL")
        payload = {
            "board_id": board_id,
            "title": post.cta[:100],
            "description": post.text,
            "media_source": {"source_type": "image_url", "url": post.image_urls[0]},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.pinterest_api_base}/pins",
                headers={"Authorization": f"Bearer {access_token}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()


class TelegramAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.telegram_api_base}/bot{access_token}/sendMessage",
                json={"chat_id": account.external_id, "text": post.text, "disable_web_page_preview": False},
            )
            response.raise_for_status()
            return response.json()


class WebsiteAdapter(SocialAdapter):
    async def publish(self, account: SocialAccount, post: GeneratedPost, access_token: str) -> dict[str, Any]:
        raise RuntimeError("Website publishing requires a WordPress or website API connector before real upload can run.")


def get_social_adapter(platform: Platform) -> SocialAdapter:
    return {
        Platform.website: WebsiteAdapter(),
        Platform.facebook: FacebookAdapter(),
        Platform.instagram: InstagramAdapter(),
        Platform.linkedin: LinkedInAdapter(),
        Platform.twitter: TwitterAdapter(),
        Platform.threads: ThreadsAdapter(),
        Platform.pinterest: PinterestAdapter(),
        Platform.telegram: TelegramAdapter(),
    }[platform]
