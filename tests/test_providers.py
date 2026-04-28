"""Tests for src/config/providers.py."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear settings cache before each test."""
    from src.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGetLlm:
    """Test get_llm() factory function."""

    def test_returns_openai_llm(self, monkeypatch):
        """get_llm() returns OpenAI LLM with correct model."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
        from src.config.providers import get_llm

        llm = get_llm()
        assert llm.model == "gpt-4o-mini"

    def test_unsupported_provider_raises(self, monkeypatch):
        """Unsupported LLM provider raises ValueError."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("LLM_PROVIDER", "unsupported")
        from src.config.providers import get_llm

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm()


class TestGetEmbedModel:
    """Test get_embed_model() factory function."""

    def test_returns_openai_embedding(self, monkeypatch):
        """get_embed_model() returns OpenAIEmbedding with correct model."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("EMBED_PROVIDER", "openai")
        monkeypatch.setenv("EMBED_MODEL", "text-embedding-3-small")
        from src.config.providers import get_embed_model

        embed = get_embed_model()
        assert embed.model_name == "text-embedding-3-small"

    def test_unsupported_provider_raises(self, monkeypatch):
        """Unsupported embedding provider raises ValueError."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("EMBED_PROVIDER", "unsupported")
        from src.config.providers import get_embed_model

        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_embed_model()


class TestGetVectorStore:
    """Test get_vector_store() factory function."""

    @patch("src.config.providers.AsyncQdrantClient")
    @patch("src.config.providers.QdrantClient")
    def test_returns_qdrant_vector_store(self, mock_sync, mock_async, monkeypatch):
        """get_vector_store() returns QdrantVectorStore with hybrid enabled."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("QDRANT_HOST", "localhost")
        monkeypatch.setenv("QDRANT_PORT", "6333")
        mock_sync.return_value = MagicMock()
        mock_async.return_value = MagicMock()

        from src.config.providers import get_vector_store

        vs = get_vector_store()
        assert vs is not None
        mock_sync.assert_called_once_with(host="localhost", port=6333)
        mock_async.assert_called_once_with(host="localhost", port=6333)

    @patch("src.config.providers.AsyncQdrantClient")
    @patch("src.config.providers.QdrantClient")
    def test_uses_custom_host_and_port(self, mock_sync, mock_async, monkeypatch):
        """get_vector_store() uses custom host/port from settings."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("QDRANT_HOST", "qdrant-server")
        monkeypatch.setenv("QDRANT_PORT", "7777")
        mock_sync.return_value = MagicMock()
        mock_async.return_value = MagicMock()

        from src.config.providers import get_vector_store

        get_vector_store()
        mock_sync.assert_called_once_with(host="qdrant-server", port=7777)
        mock_async.assert_called_once_with(host="qdrant-server", port=7777)


class TestPackageExports:
    """Test that providers are importable from src.config."""

    def test_all_factories_importable(self, monkeypatch):
        """All factory functions importable from src.config."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from src.config import get_embed_model, get_llm, get_vector_store

        assert callable(get_llm)
        assert callable(get_embed_model)
        assert callable(get_vector_store)
