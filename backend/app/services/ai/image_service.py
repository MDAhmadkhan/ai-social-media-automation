import base64

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.services.storage.adapters import get_storage_adapter

settings = get_settings()


class ImageService:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for image generation")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, prompt: str, kind: str) -> str:
        result = await self.client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
        image = result.data[0]
        if not image.b64_json:
            raise RuntimeError("Image provider returned no image data")
        return get_storage_adapter().save_bytes(base64.b64decode(image.b64_json), "image/png", "png")
