"""Tests for Settings.parse_cors_origins validator — ensures fragile JSON-only
parsing can't crash the app at import time again."""

import pytest

from app.config import Settings

REQUIRED_ENV = {
    "GEMINI_API_KEY": "test",
    "QDRANT_URL": "http://qdrant.test:6333",
    "DATABASE_URL": "postgresql+asyncpg://u:p@h/d",
    "S3_ENDPOINT_URL": "https://r2.test",
    "S3_ACCESS_KEY_ID": "k",
    "S3_SECRET_ACCESS_KEY": "s",
}


@pytest.fixture
def base_env(monkeypatch):
    """Set all required env vars; leave CORS_ORIGINS free for each test."""
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    return monkeypatch


@pytest.mark.parametrize(
    "raw,expected",
    [
        # JSON array (the documented format)
        ('["https://a.com","https://b.com"]', ["https://a.com", "https://b.com"]),
        # Comma-separated — the format that kept breaking in Fly secrets
        ("https://a.com,https://b.com", ["https://a.com", "https://b.com"]),
        # Single URL — the shape a shell often produces after losing brackets
        ("https://a.com", ["https://a.com"]),
        # Whitespace tolerance
        ("  https://a.com , https://b.com  ", ["https://a.com", "https://b.com"]),
        # JSON with whitespace inside
        ('[ "https://a.com" , "https://b.com" ]', ["https://a.com", "https://b.com"]),
    ],
)
def test_cors_origins_accepts_multiple_formats(base_env, raw, expected):
    base_env.setenv("CORS_ORIGINS", raw)
    assert Settings().cors_origins == expected


def test_cors_origins_empty_falls_back_to_default(base_env):
    base_env.setenv("CORS_ORIGINS", "")
    assert Settings().cors_origins == ["http://localhost:3000"]


def test_cors_origins_unset_uses_default(base_env):
    assert Settings().cors_origins == ["http://localhost:3000"]


def test_cors_origins_malformed_json_raises(base_env):
    base_env.setenv("CORS_ORIGINS", '["unclosed')
    with pytest.raises(Exception):
        Settings()


def test_cors_origins_non_array_json_raises(base_env):
    base_env.setenv("CORS_ORIGINS", '{"foo": "bar"}')
    with pytest.raises(Exception):
        Settings()
