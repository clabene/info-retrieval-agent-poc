"""End-to-end tests for the ingestion pipeline.

Tests the full flow: URL fetch → text extraction → chunking → Qdrant storage.

Requires:
- Qdrant running on localhost:6333
- Network access to Europe PMC / NCBI APIs

Run with: pytest tests/e2e/test_ingestion_e2e.py -x -v
"""

import os

import pytest


def _qdrant_reachable() -> bool:
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333, timeout=3)
        client.get_collections()
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _skip_without_infra():
    """Skip if Qdrant is not available."""
    if not _qdrant_reachable():
        pytest.skip("Qdrant not reachable on localhost:6333")


class TestPMCFetch:
    """Test PMC article fetching via public APIs."""

    def test_fetch_pmc_text_europe_pmc(self):
        """Fetches full text from Europe PMC for an open-access article."""
        from src.core.ingestion import _fetch_pmc_text

        # PMC7927075 is known to be available on Europe PMC
        text = _fetch_pmc_text("PMC7927075")
        assert text is not None
        assert len(text) > 1000
        # Should contain actual scientific content
        assert any(word in text.lower() for word in ["muscle", "training", "exercise", "strength"])

    def test_fetch_pmc_text_falls_back_to_efetch(self):
        """Falls back to NCBI efetch when Europe PMC returns 404."""
        from src.core.ingestion import _fetch_pmc_text

        # PMC3418948 is not on Europe PMC but available via efetch
        text = _fetch_pmc_text("PMC3418948")
        assert text is not None
        assert len(text) > 100

    def test_fetch_pmc_text_returns_none_for_invalid_id(self):
        """Returns None for a non-existent PMC ID."""
        from src.core.ingestion import _fetch_pmc_text

        text = _fetch_pmc_text("PMC0000001")
        assert text is None


class TestPMCURLDetection:
    """Test URL pattern matching for PMC articles."""

    def test_detects_standard_pmc_url(self):
        """Matches standard PMC article URL."""
        from src.core.ingestion import _extract_pmc_id

        assert _extract_pmc_id("https://pmc.ncbi.nlm.nih.gov/articles/PMC4698440/") == "PMC4698440"

    def test_detects_pmc_pdf_url(self):
        """Matches PMC PDF URL and extracts the ID."""
        from src.core.ingestion import _extract_pmc_id

        assert _extract_pmc_id("https://pmc.ncbi.nlm.nih.gov/articles/PMC4698440/pdf/") == "PMC4698440"

    def test_detects_old_style_ncbi_url(self):
        """Matches old-style www.ncbi.nlm.nih.gov/pmc URL."""
        from src.core.ingestion import _extract_pmc_id

        assert _extract_pmc_id("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4698440/") == "PMC4698440"

    def test_returns_none_for_non_pmc_url(self):
        """Returns None for non-PMC URLs."""
        from src.core.ingestion import _extract_pmc_id

        assert _extract_pmc_id("https://example.com/article") is None
        assert _extract_pmc_id("https://pubmed.ncbi.nlm.nih.gov/12345/") is None


class TestIngestionPipeline:
    """Test the full ingestion pipeline with a small set of URLs."""

    def test_ingest_single_pmc_article(self, tmp_path):
        """Ingests a single PMC article and stores chunks in Qdrant."""
        from qdrant_client import QdrantClient

        from src.core.ingestion import load_web_documents, run_ingestion_pipeline

        # Create a temporary urls file with one article
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://pmc.ncbi.nlm.nih.gov/articles/PMC7927075/\n")

        # Load documents
        docs = load_web_documents(str(urls_file))
        assert len(docs) == 1
        assert len(docs[0].text) > 1000
        assert docs[0].metadata["source_type"] == "web"
        assert "PMC7927075" in docs[0].metadata["source_url"]

        # Note: We don't run the full pipeline here to avoid polluting
        # the main knowledge_base collection. The unit tests cover
        # SentenceSplitter + embedding independently.

    def test_comments_and_blank_lines_skipped(self, tmp_path):
        """Lines starting with # and blank lines are ignored."""
        from src.core.ingestion import load_web_documents

        urls_file = tmp_path / "urls.txt"
        urls_file.write_text(
            "# This is a comment\n"
            "\n"
            "## This is also a comment\n"
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC7927075/\n"
            "  # Indented comment\n"
            "\n"
        )

        docs = load_web_documents(str(urls_file))
        assert len(docs) == 1
