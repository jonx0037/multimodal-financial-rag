from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Gemini API
    gemini_api_key: str

    # Qdrant Cloud
    qdrant_url: str
    qdrant_api_key: str = ""

    # PostgreSQL — Fly.io sets postgres://, we need postgresql+asyncpg://
    database_url: str

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # asyncpg doesn't accept sslmode — strip it (Fly internal traffic is unencrypted)
        if "?sslmode=" in url:
            url = url.split("?sslmode=")[0]
        elif "&sslmode=" in url:
            url = url.replace("&sslmode=disable", "")
        return url

    # Object Storage (S3/R2)
    s3_endpoint_url: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket_name: str = "financial-docs"

    # App — use JSON array format in .env: ["http://localhost:3000"]
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
