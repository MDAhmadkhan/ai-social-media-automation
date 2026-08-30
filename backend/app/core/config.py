from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Social Media Automation"
    environment: Literal["local", "staging", "production"] = "local"
    api_v1_prefix: str = "/api/v1"
    public_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"

    mongodb_uri: str = "mongodb://mongo:27017"
    mongodb_db: str = "ai_social_media_automation"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = Field(min_length=32, default="change-this-secret-with-at-least-32-characters")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    encryption_key: str = Field(
        min_length=32,
        default="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        description="Use `python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`.",
    )

    google_client_id: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    default_ai_provider: Literal["openai", "gemini"] = "openai"
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_models: str = "gemini-2.5-flash"

    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket: str | None = None
    local_storage_path: str = "storage"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    notification_from_email: str = "notifications@example.com"

    rate_limit: str = "100/minute"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    facebook_graph_version: str = "v21.0"
    twitter_api_base: AnyHttpUrl = "https://api.twitter.com/2"
    linkedin_api_base: AnyHttpUrl = "https://api.linkedin.com/v2"
    telegram_api_base: AnyHttpUrl = "https://api.telegram.org"
    pinterest_api_base: AnyHttpUrl = "https://api.pinterest.com/v5"
    threads_api_base: AnyHttpUrl = "https://graph.threads.net"

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
