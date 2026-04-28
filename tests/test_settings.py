"""Tests for src/config/settings.py."""

import pytest
from pydantic import ValidationError


class TestSettings:
    """Test Settings class behavior."""

    def test_loads_with_valid_api_key(self, monkeypatch):
        """Settings load successfully when OPENAI_API_KEY is provided."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        from src.config.settings import Settings

        s = Settings()
        assert s.openai_api_key == "sk-test-key-123"

    def test_defaults_are_correct(self, monkeypatch):
        """All defaults resolve correctly when only OPENAI_API_KEY is set."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        # Clear any local .env interference
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("ZEN_API_KEY", raising=False)
        monkeypatch.delenv("EMBED_PROVIDER", raising=False)
        monkeypatch.delenv("EMBED_MODEL", raising=False)
        monkeypatch.delenv("EMBED_DIMS", raising=False)
        from src.config.settings import Settings

        s = Settings(_env_file=None)
        assert s.llm_provider == "openai"
        assert s.llm_model == "gpt-4o-mini"
        assert s.embed_provider == "openai"
        assert s.embed_model == "text-embedding-3-small"
        assert s.embed_dims == 1536
        assert s.qdrant_host == "localhost"
        assert s.qdrant_port == 6333
        assert s.zen_api_key == ""

    def test_missing_openai_key_raises_when_provider_is_openai(self, monkeypatch):
        """Missing OPENAI_API_KEY raises ValidationError when provider needs it."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        from src.config.settings import Settings

        with pytest.raises(ValidationError, match="OPENAI_API_KEY is required"):
            Settings(_env_file=None)

    def test_empty_openai_key_raises_when_provider_is_openai(self, monkeypatch):
        """Empty string OPENAI_API_KEY raises ValidationError when OpenAI needed."""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        from src.config.settings import Settings

        with pytest.raises(ValidationError, match="OPENAI_API_KEY is required"):
            Settings()

    def test_no_openai_key_ok_when_using_zen_and_huggingface(self, monkeypatch):
        """No OPENAI_API_KEY needed when using zen+huggingface (fully OpenAI-free)."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "zen")
        monkeypatch.setenv("ZEN_API_KEY", "zen-key")
        monkeypatch.setenv("EMBED_PROVIDER", "huggingface")
        monkeypatch.setenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
        monkeypatch.setenv("EMBED_DIMS", "384")
        from src.config.settings import Settings

        s = Settings(_env_file=None)
        assert s.llm_provider == "zen"
        assert s.embed_provider == "huggingface"
        assert s.embed_dims == 384

    def test_zen_without_key_raises(self, monkeypatch):
        """ZEN_API_KEY required when LLM_PROVIDER=zen."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_PROVIDER", "zen")
        monkeypatch.setenv("ZEN_API_KEY", "")
        from src.config.settings import Settings

        with pytest.raises(ValidationError, match="ZEN_API_KEY is required"):
            Settings()

    def test_custom_values_override_defaults(self, monkeypatch):
        """Custom environment values override defaults."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-custom")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("QDRANT_HOST", "qdrant-server")
        monkeypatch.setenv("QDRANT_PORT", "6334")
        from src.config.settings import Settings

        s = Settings()
        assert s.llm_model == "gpt-4o"
        assert s.qdrant_host == "qdrant-server"
        assert s.qdrant_port == 6334

    def test_get_settings_returns_instance(self, monkeypatch):
        """get_settings() returns a Settings instance."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from src.config.settings import get_settings

        get_settings.cache_clear()
        s = get_settings()
        assert s.openai_api_key == "sk-test"

    def test_settings_importable_from_config_package(self, monkeypatch):
        """Settings and get_settings are importable from src.config."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from src.config import Settings, get_settings

        assert Settings is not None
        assert get_settings is not None
