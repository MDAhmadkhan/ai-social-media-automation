import hashlib
from urllib.parse import urldefrag, urljoin, urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.models.enums import WebsiteType


class WebPage:
    def __init__(self, url: str, title: str, description: str | None, keywords: list[str], text: str, image_url: str | None = None) -> None:
        self.url = url
        self.title = title
        self.description = description
        self.keywords = keywords
        self.text = text
        self.image_url = image_url
        self.source_hash = hashlib.sha256(text.encode()).hexdigest()


class WebReader:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": "AISocialAutomationBot/1.0"})

    async def discover_urls(self, url: str, website_type: WebsiteType) -> list[str]:
        if website_type == WebsiteType.rss:
            response = await self.client.get(url)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            return [entry.link for entry in feed.entries if getattr(entry, "link", None)]
        if website_type == WebsiteType.sitemap:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "xml")
            return [loc.get_text(strip=True) for loc in soup.find_all("loc")]
        if website_type == WebsiteType.wordpress:
            api = url.rstrip("/") + "/wp-json/wp/v2/posts?per_page=10&_fields=link"
            response = await self.client.get(api)
            response.raise_for_status()
            return [post["link"] for post in response.json() if post.get("link")]
        if website_type == WebsiteType.custom:
            return await self._discover_internal_links(url)
        return [url]

    async def read(self, url: str) -> WebPage:
        response = await self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        title = (soup.title.string.strip() if soup.title and soup.title.string else None) or url
        description = self._meta(soup, "description") or self._property(soup, "og:description")
        keywords = [item.strip() for item in (self._meta(soup, "keywords") or "").split(",") if item.strip()]
        image_url = self._property(soup, "og:image") or self._meta(soup, "twitter:image")
        if image_url:
            image_url = urljoin(url, image_url)
        canonical = soup.find("link", rel="canonical")
        canonical_url = urljoin(url, canonical["href"]) if canonical and canonical.get("href") else url
        text = " ".join(soup.get_text(" ").split())
        return WebPage(canonical_url, title[:300], description, keywords[:30], text[:50000], image_url)

    def _meta(self, soup: BeautifulSoup, name: str) -> str | None:
        node = soup.find("meta", attrs={"name": name})
        return node.get("content", "").strip() if node else None

    def _property(self, soup: BeautifulSoup, prop: str) -> str | None:
        node = soup.find("meta", attrs={"property": prop})
        return node.get("content", "").strip() if node else None

    async def _discover_internal_links(self, url: str) -> list[str]:
        response = await self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        base = urlparse(str(response.url))
        discovered: list[str] = []
        seen: set[str] = set()

        def add(candidate: str) -> None:
            absolute = urljoin(str(response.url), candidate)
            absolute, _fragment = urldefrag(absolute)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
                return
            if any(skip in parsed.path.lower() for skip in ["/privacy", "/terms", "/contact", "/about", "/disclaimer"]):
                return
            if absolute not in seen:
                seen.add(absolute)
                discovered.append(absolute)

        add(str(response.url))
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                add(href)
        return discovered[:150]
