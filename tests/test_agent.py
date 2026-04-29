"""Tests for src/core/agent.py."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear settings cache before each test."""
    from src.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestBuildQueryEngineTool:
    """Test build_query_engine_tool() function."""

    @patch("src.core.agent.VectorStoreIndex")
    @patch("src.core.agent.get_vector_store")
    def test_returns_query_engine_tool(self, mock_get_vs, mock_index_cls, monkeypatch):
        """build_query_engine_tool() returns a QueryEngineTool."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_vs = MagicMock()
        mock_get_vs.return_value = mock_vs

        mock_index = MagicMock()
        mock_index_cls.from_vector_store.return_value = mock_index
        mock_query_engine = MagicMock()
        mock_index.as_query_engine.return_value = mock_query_engine

        from src.core.agent import build_query_engine_tool

        tool = build_query_engine_tool()

        assert tool.metadata.name == "knowledge_base"
        assert "knowledge base" in tool.metadata.description.lower()
        mock_index.as_query_engine.assert_called_once_with(
            similarity_top_k=5,
            sparse_top_k=12,
            vector_store_query_mode="hybrid",
        )


class TestBuildAgent:
    """Test build_agent() function."""

    @patch("src.core.agent.FunctionAgent")
    @patch("src.core.agent.build_query_engine_tool")
    @patch("src.core.agent.LlamaSettings")
    @patch("src.core.agent.get_embed_model")
    @patch("src.core.agent.get_llm")
    def test_returns_function_agent(
        self, mock_get_llm, mock_get_embed, mock_settings, mock_build_tool, mock_agent_cls, monkeypatch
    ):
        """build_agent() constructs a FunctionAgent with correct params."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        mock_get_embed.return_value = MagicMock()

        mock_tool = MagicMock()
        mock_tool.metadata.name = "knowledge_base"
        mock_build_tool.return_value = mock_tool

        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent

        from src.core.agent import build_agent

        result = build_agent()

        assert result is mock_agent
        mock_get_llm.assert_called_once()
        mock_build_tool.assert_called_once()
        mock_agent_cls.assert_called_once()
        call_kwargs = mock_agent_cls.call_args[1]
        assert call_kwargs["tools"] == [mock_tool]
        assert call_kwargs["llm"] is mock_llm
        assert "information retrieval" in call_kwargs["system_prompt"].lower()
