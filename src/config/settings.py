"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Typed, validated application configuration.

    All values are read from environment variables (or .env file).
    OPENAI_API_KEY is required; all others have sensible defaults.
    """

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    openai_api_key: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    embed_provider: str = "openai"
    embed_model: str = "text-embedding-3-small"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    @field_validator("openai_api_key")
    @classmethod
    def openai_api_key_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("OPENAI_API_KEY must not be empty")
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
