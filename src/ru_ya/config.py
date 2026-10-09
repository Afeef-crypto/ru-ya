from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str | None:
    for candidate in (Path(".env"), Path(__file__).resolve().parents[2] / ".env"):
        if candidate.exists():
            return str(candidate)
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    ruya_llm_base_url: str = "https://openrouter.ai/api/v1"
    ruya_llm_api_key: str = ""
    ruya_llm_model: str = "openai/gpt-4o-mini"
    ruya_llm_http_referer: str = "http://localhost:3000"
    ruya_llm_app_title: str = "Ru-ya"
    ruya_embedding_model: str = "BAAI/bge-m3"
    redis_url: str = "redis://localhost:6379/0"
    next_public_api_base: str = "http://localhost:8000/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
