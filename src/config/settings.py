"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Typed, validated application configuration.

    All values are read from environment variables (or .env file).
    OPENAI_API_KEY is required when using OpenAI for LLM or embeddings.
    """

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    openai_api_key: str = ""
    zen_api_key: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_base: str = ""
    embed_provider: str = "openai"
    embed_model: str = "text-embedding-3-small"
    embed_dims: int = 1536
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        """Ensure required API keys are present based on provider choices."""
        needs_openai = self.llm_provider == "openai" or self.embed_provider == "openai"
        if needs_openai and not self.openai_api_key.strip():
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai or EMBED_PROVIDER=openai. "
                "Set it in .env or switch to alternative providers (zen, huggingface)."
            )
        if self.llm_provider == "zen" and not self.zen_api_key.strip():
            raise ValueError("ZEN_API_KEY is required when LLM_PROVIDER=zen")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
