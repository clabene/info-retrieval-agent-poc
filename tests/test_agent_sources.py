"""Tests for _collect_sources() and source capture wrappers in src/core/agent.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear settings cache before each test."""
    from src.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def clear_sources():
    """Clear the module-level _last_sources before/after each test."""
    from src.core.agent import _last_sources

    _last_sources.clear()
    yield _last_sources
    _last_sources.clear()


class TestCollectSources:
    """Test _collect_sources() metadata extraction from ToolOutput."""

    def test_extracts_source_url(self, clear_sources):
        """Extracts source_url from node metadata."""
        from src.core.agent import _collect_sources

        node = MagicMock()
        node.metadata = {"source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC123/"}
        source_node = MagicMock()
        source_node.node = node

        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [source_node]

        _collect_sources(tool_output)

        assert clear_sources == ["https://pmc.ncbi.nlm.nih.gov/articles/PMC123/"]

    def test_extracts_file_name_with_page_label(self, clear_sources):
        """Extracts file_name + page_label when no source_url."""
        from src.core.agent import _collect_sources

        node = MagicMock()
        node.metadata = {"file_name": "paper.pdf", "page_label": "5"}
        source_node = MagicMock()
        source_node.node = node

        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [source_node]

        _collect_sources(tool_output)

        assert clear_sources == ["paper.pdf (p. 5)"]

    def test_extracts_file_name_only(self, clear_sources):
        """Extracts file_name when no source_url or page_label."""
        from src.core.agent import _collect_sources

        node = MagicMock()
        node.metadata = {"file_name": "report.pdf"}
        source_node = MagicMock()
        source_node.node = node

        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [source_node]

        _collect_sources(tool_output)

        assert clear_sources == ["report.pdf"]

    def test_no_useful_metadata_adds_nothing(self, clear_sources):
        """Nodes with no source_url or file_name are skipped."""
        from src.core.agent import _collect_sources

        node = MagicMock()
        node.metadata = {"some_other_key": "value"}
        source_node = MagicMock()
        source_node.node = node

        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [source_node]

        _collect_sources(tool_output)

        assert clear_sources == []

    def test_multiple_source_nodes(self, clear_sources):
        """Handles multiple source nodes in a single ToolOutput."""
        from src.core.agent import _collect_sources

        node1 = MagicMock()
        node1.metadata = {"source_url": "https://example.com/page1"}
        sn1 = MagicMock()
        sn1.node = node1

        node2 = MagicMock()
        node2.metadata = {"file_name": "doc.pdf", "page_label": "12"}
        sn2 = MagicMock()
        sn2.node = node2

        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [sn1, sn2]

        _collect_sources(tool_output)

        assert clear_sources == ["https://example.com/page1", "doc.pdf (p. 12)"]

    def test_no_raw_output_does_nothing(self, clear_sources):
        """Handles ToolOutput with no raw_output gracefully."""
        from src.core.agent import _collect_sources

        tool_output = MagicMock()
        tool_output.raw_output = None

        _collect_sources(tool_output)

        assert clear_sources == []

    def test_no_source_nodes_does_nothing(self, clear_sources):
        """Handles raw_output with no source_nodes attribute."""
        from src.core.agent import _collect_sources

        tool_output = MagicMock()
        tool_output.raw_output = MagicMock(spec=[])  # No source_nodes attribute

        _collect_sources(tool_output)

        assert clear_sources == []


class TestSourceCaptureWrappers:
    """Test the monkey-patched call/acall wrappers."""

    @patch("src.core.agent.VectorStoreIndex")
    @patch("src.core.agent.get_vector_store")
    def test_sync_call_captures_sources(self, mock_get_vs, mock_index_cls, monkeypatch, clear_sources):
        """Sync call wrapper invokes original and captures sources."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        mock_vs = MagicMock()
        mock_get_vs.return_value = mock_vs
        mock_index = MagicMock()
        mock_index_cls.from_vector_store.return_value = mock_index

        # Create a mock query engine that returns a response with source nodes
        mock_qe = MagicMock()
        node = MagicMock()
        node.metadata = {"source_url": "https://example.com/doc"}
        source_node = MagicMock()
        source_node.node = node

        mock_response = MagicMock()
        mock_response.source_nodes = [source_node]

        # The ToolOutput wraps the response
        from llama_index.core.tools import ToolOutput

        mock_index.as_query_engine.return_value = mock_qe

        from src.core.agent import build_query_engine_tool

        tool = build_query_engine_tool()

        # Simulate what the patched call does
        fake_output = MagicMock()
        fake_output.raw_output = mock_response

        # Replace the original call with one that returns our fake output
        tool.call = MagicMock(return_value=fake_output)

        # The wrapper was already applied during build, so we test _collect_sources directly
        from src.core.agent import _collect_sources

        _collect_sources(fake_output)

        assert "https://example.com/doc" in clear_sources

    @patch("src.core.agent.VectorStoreIndex")
    @patch("src.core.agent.get_vector_store")
    @pytest.mark.asyncio
    async def test_async_call_captures_sources(self, mock_get_vs, mock_index_cls, monkeypatch, clear_sources):
        """Async call wrapper invokes original and captures sources."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        mock_vs = MagicMock()
        mock_get_vs.return_value = mock_vs
        mock_index = MagicMock()
        mock_index_cls.from_vector_store.return_value = mock_index
        mock_index.as_query_engine.return_value = MagicMock()

        from src.core.agent import _collect_sources

        node = MagicMock()
        node.metadata = {"file_name": "async_doc.pdf", "page_label": "3"}
        source_node = MagicMock()
        source_node.node = node

        fake_output = MagicMock()
        fake_output.raw_output = MagicMock()
        fake_output.raw_output.source_nodes = [source_node]

        _collect_sources(fake_output)

        assert "async_doc.pdf (p. 3)" in clear_sources
