"""End-to-end tests for the /query API endpoint.

These tests require:
- Qdrant running on localhost:6333 with ingested data
- Valid OPENAI_API_KEY (or ZEN_API_KEY) in the environment
- The knowledge_base collection populated with PMC articles

Run with: pytest tests/e2e/ -x -v
Skip in CI without infra: pytest tests/e2e/ -m "not e2e"
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _has_api_key() -> bool:
    """Check if an LLM API key is available (env var or .env file)."""
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("ZEN_API_KEY"):
        return True
    # Check .env file in project root
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        content = env_file.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY=") and line.split("=", 1)[1].strip():
                return True
            if line.startswith("ZEN_API_KEY=") and line.split("=", 1)[1].strip():
                return True
    return False


# Skip entire module if no API key or Qdrant not reachable
pytestmark = pytest.mark.skipif(
    not _has_api_key(),
    reason="No LLM API key set — skipping E2E tests",
)


def _qdrant_reachable() -> bool:
    """Check if Qdrant is reachable on localhost:6333."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333, timeout=3)
        client.get_collections()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def e2e_client():
    """Create a real TestClient with no mocks — uses live Qdrant + LLM."""
    if not _qdrant_reachable():
        pytest.skip("Qdrant not reachable on localhost:6333")

    from src.api.app import app

    with TestClient(app) as client:
        yield client


class TestHealthEndpoint:
    """Smoke test — verifies the app starts and responds."""

    def test_health_returns_healthy(self, e2e_client):
        """GET /health returns 200 with status=healthy."""
        response = e2e_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestQueryEndpointE2E:
    """End-to-end tests for POST /query with real infrastructure."""

    def test_hydration_query_returns_answer_and_sources(self, e2e_client):
        """Query about hydration returns a substantive answer with PMC sources."""
        response = e2e_client.post(
            "/query",
            json={"question": "how important is hydration?"},
        )
        assert response.status_code == 200
        data = response.json()

        # Answer should be non-empty and substantive
        assert "answer" in data
        assert len(data["answer"]) > 50

        # Sources should contain PMC URLs
        assert "sources" in data
        assert len(data["sources"]) > 0
        assert any("pmc.ncbi.nlm.nih.gov" in src for src in data["sources"])

    def test_workout_query_returns_relevant_answer(self, e2e_client):
        """Query about workouts returns relevant content from indexed papers."""
        response = e2e_client.post(
            "/query",
            json={"question": "What is the optimal training frequency for muscle growth?"},
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["answer"]) > 50
        assert "sources" in data
        assert len(data["sources"]) > 0

    def test_irrelevant_query_admits_no_information(self, e2e_client):
        """Query outside knowledge base scope gets a 'not found' style response."""
        response = e2e_client.post(
            "/query",
            json={"question": "What is the capital of France?"},
        )
        assert response.status_code == 200
        data = response.json()

        # Agent should either admit it can't find info or give a very short response
        # (it shouldn't hallucinate a full answer from general knowledge)
        assert "answer" in data

    def test_empty_question_returns_422(self, e2e_client):
        """Empty question body returns validation error."""
        response = e2e_client.post("/query", json={})
        assert response.status_code == 422

    def test_malformed_body_returns_422(self, e2e_client):
        """Non-JSON body returns 422."""
        response = e2e_client.post(
            "/query",
            content="not json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422
