"""Tests for src/config/settings.py."""

import pytest
from pydantic import ValidationError


class TestSettings:
    """Test Settings class behavior."""

    def test_loads_with_valid_api_key(self, monkeypatch):
        """Settings load successfully when OPENAI_API_KEY is provided."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        # Clear lru_cache between tests
        from src.config.settings import Settings

        s = Settings()
        assert s.openai_api_key == "sk-test-key-123"

    def test_defaults_are_correct(self, monkeypatch):
        """All defaults resolve correctly when only OPENAI_API_KEY is set."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        from src.config.settings import Settings

        s = Settings()
        assert s.llm_provider == "openai"
        assert s.llm_model == "gpt-4o-mini"
        assert s.embed_provider == "openai"
        assert s.embed_model == "text-embedding-3-small"
        assert s.qdrant_host == "localhost"
        assert s.qdrant_port == 6333

    def test_missing_api_key_raises_validation_error(self, monkeypatch):
        """Missing OPENAI_API_KEY raises ValidationError."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from src.config.settings import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_empty_api_key_raises_validation_error(self, monkeypatch):
        """Empty string OPENAI_API_KEY raises ValidationError."""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        from src.config.settings import Settings

        with pytest.raises(ValidationError, match="must not be empty"):
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
