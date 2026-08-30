import json
from abc import ABC, abstractmethod
from typing import Any

import google.generativeai as genai
import httpx
from google.api_core.exceptions import GoogleAPIError
from openai import APIStatusError, AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.models.domain import BrandSettings, ContentItem
from app.models.enums import Platform

settings = get_settings()


class AIProvider(ABC):
    @abstractmethod
    async def generate_social_bundle(
        self, content: ContentItem, brand: BrandSettings, platforms: list[Platform]
    ) -> dict[str, Any]:
        raise NotImplementedError


def build_prompt(content: ContentItem, brand: BrandSettings, platforms: list[Platform]) -> str:
    return f"""
You are a senior social media strategist. Generate multilingual-ready campaign copy from the webpage content.
Return strict JSON with keys: seo_summary, short_summary, long_summary, callout_points, carousel_text, quote_card_text, posts.
posts must be an object keyed by platform values: {[p.value for p in platforms]}.
Each post must include text, hashtags array, and cta.

Brand voice: {brand.brand_voice}
Language: {brand.language}
Tone: {brand.tone}
Emoji level 0-3: {brand.emoji_level}
Hashtag count: {brand.hashtag_count}
Default CTA: {brand.default_cta}

Title: {content.title}
Meta description: {content.meta_description}
Keywords: {content.keywords}
Article text:
{content.raw_text[:16000]}
"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return text


def _interaction_output_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    parts: list[str] = []
    for step in data.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for item in step.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item["text"])
    return "\n".join(parts)


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI provider")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_social_bundle(self, content: ContentItem, brand: BrandSettings, platforms: list[Platform]) -> dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Return valid JSON only. Respect platform character limits."},
                    {"role": "user", "content": build_prompt(content, brand, platforms)},
                ],
                temperature=0.7,
            )
            return json.loads(response.choices[0].message.content or "{}")
        except APIStatusError as exc:
            if exc.status_code == 429:
                raise RuntimeError("OpenAI quota exceeded. Add billing/credits or use another API key.") from exc
            raise RuntimeError(f"OpenAI API error: {exc.status_code}") from exc
        except OpenAIError as exc:
            raise RuntimeError("OpenAI request failed. Check your API key, model access, and billing status.") from exc


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider")
        self.api_key = settings.gemini_api_key
        self.use_interactions_api = self.api_key.startswith("AQ.")
        self.model = None
        if not self.use_interactions_api:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)

    async def generate_social_bundle(self, content: ContentItem, brand: BrandSettings, platforms: list[Platform]) -> dict[str, Any]:
        try:
            if self.use_interactions_api:
                return await self._generate_with_interactions_api(content, brand, platforms)
            if self.model is None:
                raise RuntimeError("Gemini model was not initialized")
            response = await self.model.generate_content_async(
                build_prompt(content, brand, platforms) + "\nReturn JSON only, without markdown fences."
            )
            return json.loads(_clean_json_text(response.text))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON. Try again with fewer platforms.") from exc
        except GoogleAPIError as exc:
            raise RuntimeError(f"Gemini API error: {exc.message}") from exc
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError("Gemini request failed. Check your Gemini API key, model access, quota, and safety settings.") from exc

    async def _generate_with_interactions_api(self, content: ContentItem, brand: BrandSettings, platforms: list[Platform]) -> dict[str, Any]:
        prompt = build_prompt(content, brand, platforms) + "\nReturn JSON only, without markdown fences."
        data = await self._call_interactions_with_fallback(prompt)
        text = _interaction_output_text(data)
        if not text:
            raise RuntimeError("Gemini returned an empty response. Try again or choose a different Gemini model.")
        return json.loads(_clean_json_text(text))

    async def _call_interactions_with_fallback(self, prompt: str) -> dict[str, Any]:
        models = [settings.gemini_model]
        models.extend(model.strip() for model in settings.gemini_fallback_models.split(",") if model.strip())
        last_detail = ""
        async with httpx.AsyncClient(timeout=90) as client:
            for model in dict.fromkeys(models):
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/interactions",
                    headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                    json={"model": model, "input": prompt},
                )
                if response.status_code < 400:
                    return response.json()
                last_detail = self._api_error_detail(response)
                if not self._should_try_fallback(last_detail):
                    break
        raise RuntimeError(f"Gemini API error: {last_detail or 'request failed'}")

    def _api_error_detail(self, response: httpx.Response) -> str:
        try:
            return response.json().get("error", {}).get("message") or response.text
        except ValueError:
            return response.text

    def _should_try_fallback(self, detail: str) -> bool:
        lowered = detail.lower()
        return any(term in lowered for term in ["high demand", "try again later", "unavailable", "resource exhausted", "temporarily"])


def get_ai_provider() -> AIProvider:
    if settings.default_ai_provider == "gemini":
        return GeminiProvider()
    return OpenAIProvider()
