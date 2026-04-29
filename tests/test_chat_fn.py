"""Tests for the Gradio chat function in src/api/app.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear settings cache before each test."""
    from src.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_sources():
    """Reset per-request sources before/after each test."""
    from src.core.agent import init_sources

    init_sources()
    yield
    init_sources()


class TestChatFunction:
    """Test the Gradio _chat_fn() handler."""

    @pytest.mark.asyncio
    async def test_empty_message_returns_empty_string(self):
        """Empty or whitespace messages return empty string."""
        from src.api.app import _chat_fn

        assert await _chat_fn("", []) == ""
        assert await _chat_fn("   ", []) == ""

    @pytest.mark.asyncio
    async def test_none_agent_returns_initialization_message(self):
        """Returns initialization message when agent is None."""
        import src.api.app as app_module

        original = app_module._agent
        app_module._agent = None
        try:
            result = await app_module._chat_fn("hello", [])
            assert "not initialized" in result.lower()
        finally:
            app_module._agent = original

    @pytest.mark.asyncio
    async def test_returns_answer_from_agent(self):
        """Returns agent response as string."""
        import src.api.app as app_module

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="This is the answer about hydration.")

        original = app_module._agent
        app_module._agent = mock_agent
        try:
            result = await app_module._chat_fn("how important is hydration?", [])
            assert "This is the answer about hydration." in result
        finally:
            app_module._agent = original

    @pytest.mark.asyncio
    async def test_appends_url_sources_as_markdown_links(self):
        """URL sources are formatted as markdown links."""
        import src.api.app as app_module
        from src.core.agent import get_last_sources

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="Answer text.")

        original = app_module._agent
        app_module._agent = mock_agent

        # Simulate sources being added during agent run
        async def fake_run(**kwargs):
            get_last_sources().append("https://pmc.ncbi.nlm.nih.gov/articles/PMC123/")
            return "Answer text."

        mock_agent.run = fake_run

        try:
            result = await app_module._chat_fn("test question", [])
            assert "Sources:" in result
            assert "[https://pmc.ncbi.nlm.nih.gov/articles/PMC123/]" in result
            assert "(https://pmc.ncbi.nlm.nih.gov/articles/PMC123/)" in result
        finally:
            app_module._agent = original

    @pytest.mark.asyncio
    async def test_appends_non_url_sources_as_plain_text(self):
        """Non-URL sources (file names) are listed without link formatting."""
        import src.api.app as app_module
        from src.core.agent import get_last_sources

        mock_agent = MagicMock()

        async def fake_run(**kwargs):
            get_last_sources().append("paper.pdf (p. 5)")
            return "Answer about paper."

        mock_agent.run = fake_run

        original = app_module._agent
        app_module._agent = mock_agent
        try:
            result = await app_module._chat_fn("question about paper", [])
            assert "Sources:" in result
            assert "- paper.pdf (p. 5)" in result
            # Should NOT be formatted as a link
            assert "[paper.pdf" not in result
        finally:
            app_module._agent = original

    @pytest.mark.asyncio
    async def test_deduplicates_sources(self):
        """Duplicate sources are deduplicated."""
        import src.api.app as app_module
        from src.core.agent import get_last_sources

        async def fake_run(**kwargs):
            get_last_sources().append("https://example.com/doc1")
            get_last_sources().append("https://example.com/doc1")
            get_last_sources().append("https://example.com/doc2")
            return "Answer."

        mock_agent = MagicMock()
        mock_agent.run = fake_run

        original = app_module._agent
        app_module._agent = mock_agent
        try:
            result = await app_module._chat_fn("test", [])
            # doc1 should appear only once
            assert result.count("example.com/doc1") == 2  # once in [] and once in ()
            assert result.count("example.com/doc2") == 2
        finally:
            app_module._agent = original

    @pytest.mark.asyncio
    async def test_error_returns_error_string(self):
        """Agent errors are returned as an error message string (not raised)."""
        import src.api.app as app_module

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(side_effect=RuntimeError("LLM connection failed"))

        original = app_module._agent
        app_module._agent = mock_agent
        try:
            result = await app_module._chat_fn("test", [])
            assert "Error:" in result
            assert "LLM connection failed" in result
        finally:
            app_module._agent = original

    @pytest.mark.asyncio
    async def test_no_sources_omits_sources_section(self):
        """When no sources are captured, the Sources section is omitted."""
        import src.api.app as app_module

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="Simple answer.")

        original = app_module._agent
        app_module._agent = mock_agent
        try:
            result = await app_module._chat_fn("test", [])
            assert "Sources:" not in result
            assert result == "Simple answer."
        finally:
            app_module._agent = original
