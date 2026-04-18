import json
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
        # asyncpg uses 'ssl' not 'sslmode' — replace for Fly internal traffic
        if "?sslmode=" in url:
            url = url.split("?sslmode=")[0] + "?ssl=disable"
        elif "&sslmode=" in url:
            url = url.replace("&sslmode=disable", "&ssl=disable")
        return url

    # Object Storage (S3/R2)
    s3_endpoint_url: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket_name: str = "financial-docs"

    # App — NoDecode skips pydantic_settings' auto-JSON parsing so our
    # validator sees the raw env string and can accept any common shape.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    log_level: str = "INFO"
    enable_explainability: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        """Accept list, JSON array string, comma-separated string, or single URL."""
        if value is None or value == "":
            return ["http://localhost:3000"]
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped[:1] in ("[", "{"):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON must be an array")
                return [str(v).strip() for v in parsed if str(v).strip()]
            return [part.strip() for part in stripped.split(",") if part.strip()]
        raise TypeError(f"cors_origins must be list or str, got {type(value).__name__}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
