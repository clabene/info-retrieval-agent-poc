"""Tests for src/core/vector_store.py."""

from unittest.mock import MagicMock, patch

import pytest
from qdrant_client.models import Distance


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear settings cache before each test."""
    from src.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestEnsureCollection:
    """Test ensure_collection() function."""

    @patch("src.core.vector_store.QdrantClient")
    def test_creates_collection_when_not_exists(self, mock_client_cls, monkeypatch):
        """Collection is created with correct params when it doesn't exist."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("EMBED_DIMS", "1536")
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False
        mock_client_cls.return_value = mock_client

        from src.core.vector_store import ensure_collection

        ensure_collection()

        mock_client.collection_exists.assert_called_once_with("knowledge_base")
        mock_client.create_collection.assert_called_once()

        # Verify vector params
        call_kwargs = mock_client.create_collection.call_args[1]
        assert call_kwargs["collection_name"] == "knowledge_base"
        vectors_config = call_kwargs["vectors_config"]
        assert vectors_config.size == 1536
        assert vectors_config.distance == Distance.COSINE
        assert "text-sparse-new" in call_kwargs["sparse_vectors_config"]

    @patch("src.core.vector_store.QdrantClient")
    def test_does_not_recreate_existing_collection(self, mock_client_cls, monkeypatch):
        """Collection is NOT recreated when it already exists."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_client_cls.return_value = mock_client

        from src.core.vector_store import ensure_collection

        ensure_collection()

        mock_client.collection_exists.assert_called_once_with("knowledge_base")
        mock_client.create_collection.assert_not_called()
        mock_client.create_payload_index.assert_not_called()

    @patch("src.core.vector_store.QdrantClient")
    def test_creates_payload_indexes(self, mock_client_cls, monkeypatch):
        """Payload indexes are created for source_type and file_name."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False
        mock_client_cls.return_value = mock_client

        from src.core.vector_store import ensure_collection

        ensure_collection()

        # Verify both payload indexes created
        index_calls = mock_client.create_payload_index.call_args_list
        assert len(index_calls) == 2

        field_names = {c[1]["field_name"] for c in index_calls}
        assert field_names == {"source_type", "file_name"}

        for c in index_calls:
            assert c[1]["collection_name"] == "knowledge_base"
            assert c[1]["field_schema"] == "keyword"

    @patch("src.core.vector_store.QdrantClient")
    def test_uses_settings_for_connection(self, mock_client_cls, monkeypatch):
        """ensure_collection uses host/port from settings."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("QDRANT_HOST", "custom-host")
        monkeypatch.setenv("QDRANT_PORT", "9999")
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_client_cls.return_value = mock_client

        from src.core.vector_store import ensure_collection

        ensure_collection()

        mock_client_cls.assert_called_once_with(host="custom-host", port=9999)
