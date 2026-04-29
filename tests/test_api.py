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

        # Build a realistic mock response with tool_calls containing source_nodes
        mock_tool_output = MagicMock()
        mock_source_node = MagicMock()
        mock_source_node.metadata = {"file_name": "guide.pdf", "page_label": "5", "source_type": "pdf"}
        mock_source_node.node.metadata = {"file_name": "guide.pdf", "page_label": "5", "source_type": "pdf"}
        mock_tool_output.raw_output.source_nodes = [mock_source_node]

        mock_tool_call = MagicMock()
        mock_tool_call.tool_output = mock_tool_output

        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "The answer is 42. Source: guide.pdf"
        mock_response.tool_calls = [mock_tool_call]

        mock_agent.run = AsyncMock(return_value=mock_response)
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


class TestExtractSources:
    """Test _extract_sources_from_tool_calls helper."""

    def test_extracts_pdf_with_page(self):
        """Extracts PDF filename with page number from tool calls."""
        from src.api.app import _extract_sources_from_tool_calls

        response = MagicMock()
        node = MagicMock()
        node.metadata = {"file_name": "guide.pdf", "page_label": "5", "source_type": "pdf"}
        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [node]
        tool_call = MagicMock()
        tool_call.tool_output = tool_output
        response.tool_calls = [tool_call]

        result = _extract_sources_from_tool_calls(response)
        assert "guide.pdf (p. 5)" in result

    def test_extracts_web_url(self):
        """Extracts URL from web source nodes."""
        from src.api.app import _extract_sources_from_tool_calls

        response = MagicMock()
        node = MagicMock()
        node.metadata = {
            "source_url": "https://example.com/page",
            "file_name": "https://example.com/page",
            "source_type": "web",
        }
        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [node]
        tool_call = MagicMock()
        tool_call.tool_output = tool_output
        response.tool_calls = [tool_call]

        result = _extract_sources_from_tool_calls(response)
        assert "https://example.com/page" in result

    def test_deduplicates_sources(self):
        """Removes duplicate sources."""
        from src.api.app import _extract_sources_from_tool_calls

        response = MagicMock()
        node1 = MagicMock()
        node1.metadata = {"file_name": "guide.pdf", "page_label": "5"}
        node2 = MagicMock()
        node2.metadata = {"file_name": "guide.pdf", "page_label": "5"}
        tool_output = MagicMock()
        tool_output.raw_output.source_nodes = [node1, node2]
        tool_call = MagicMock()
        tool_call.tool_output = tool_output
        response.tool_calls = [tool_call]

        result = _extract_sources_from_tool_calls(response)
        assert result.count("guide.pdf (p. 5)") == 1

    def test_returns_empty_when_no_tool_calls(self):
        """Returns empty list when response has no tool_calls."""
        from src.api.app import _extract_sources_from_tool_calls

        response = MagicMock(spec=[])
        result = _extract_sources_from_tool_calls(response)
        assert result == []
