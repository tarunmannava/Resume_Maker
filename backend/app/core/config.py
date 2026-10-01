from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ai_provider: str = "openai"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    max_output_tokens: int = 16384
    target_keyword_match: int = 90
    default_rewrite_mode: str = "transferable"
    queue_worker_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "backend/app/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
