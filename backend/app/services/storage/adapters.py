from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings


class LocalStorageAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_path = Path(self.settings.local_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, data: bytes, content_type: str, extension: str) -> str:
        folder = self.base_path / content_type.split("/", 1)[0]
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}.{extension.lstrip('.')}"
        path = folder / filename
        path.write_bytes(data)
        return f"{self.settings.public_base_url.rstrip('/')}/storage/{folder.name}/{filename}"


def get_storage_adapter() -> LocalStorageAdapter:
    return LocalStorageAdapter()
