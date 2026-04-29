"""Tests for src/api/app.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear settings cache before each test."""
    from src.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked agent."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    with patch("src.api.app.build_agent") as mock_build:
        mock_agent = MagicMock()

        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "The answer is 42. Source: guide.pdf"
        mock_response.tool_calls = []

        # Simulate the tool wrapper populating sources during agent.run()
        def _fake_run(**kwargs):
            from src.core.agent import init_sources, get_last_sources
            init_sources()
            get_last_sources().append("guide.pdf (p. 5)")
            return mock_response

        mock_agent.run = AsyncMock(side_effect=_fake_run)
        mock_build.return_value = mock_agent

        import src.api.app as app_module
        from src.api.app import app

        app_module._agent = mock_agent

        with TestClient(app) as c:
            yield c

        app_module._agent = None


class TestQueryEndpoint:
    """Test POST /query endpoint."""

    def test_returns_answer_with_sources(self, client):
        """POST /query returns answer and extracted sources."""
        response = client.post("/query", json={"question": "What is the meaning of life?"})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "guide.pdf (p. 5)" in data["sources"]

    def test_returns_422_on_missing_question(self, client):
        """POST /query returns 422 when question field is missing."""
        response = client.post("/query", json={})
        assert response.status_code == 422

    def test_returns_422_on_invalid_body(self, client):
        """POST /query returns 422 on invalid request body."""
        response = client.post("/query", content="not json", headers={"content-type": "application/json"})
        assert response.status_code == 422

    def test_returns_500_on_agent_error(self, client, monkeypatch):
        """POST /query returns 500 when agent raises an error."""
        import src.api.app as app_module

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(side_effect=RuntimeError("Qdrant unreachable"))
        app_module._agent = mock_agent

        response = client.post("/query", json={"question": "test"})
        assert response.status_code == 500
        assert "Qdrant unreachable" in response.json()["detail"]


class TestHealthEndpoint:
    """Test GET /health endpoint."""

    def test_returns_healthy(self, client):
        """GET /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestOpenAPIDocs:
    """Test OpenAPI docs availability."""

    def test_docs_available(self, client):
        """GET /docs returns OpenAPI documentation."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestSourceCapture:
    """Test source capture via contextvars side-effect."""

    def test_sources_populated_by_tool_wrapper(self):
        """The tool wrapper appends source URLs to per-request sources."""
        from src.core.agent import get_last_sources, init_sources

        init_sources()
        sources = get_last_sources()
        sources.append("https://example.com/article")
        sources.append("guide.pdf (p. 5)")

        assert "https://example.com/article" in get_last_sources()
        assert "guide.pdf (p. 5)" in get_last_sources()

    def test_deduplicates_sources(self):
        """Deduplication via dict.fromkeys preserves order and removes duplicates."""
        from src.core.agent import get_last_sources, init_sources

        init_sources()
        get_last_sources().extend(["a.pdf", "b.pdf", "a.pdf", "c.pdf", "b.pdf"])

        result = list(dict.fromkeys(get_last_sources()))
        assert result == ["a.pdf", "b.pdf", "c.pdf"]

    def test_init_sources_resets(self):
        """init_sources creates a fresh list for the current context."""
        from src.core.agent import get_last_sources, init_sources

        init_sources()
        get_last_sources().append("stale.pdf")
        init_sources()
        assert len(get_last_sources()) == 0
