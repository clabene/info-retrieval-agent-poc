"""Tests for src/core/ingestion.py."""

from unittest.mock import MagicMock, patch


class TestLoadPdfDocuments:
    """Test load_pdf_documents() function."""

    def test_returns_empty_list_when_directory_missing(self):
        """Returns empty list when PDF directory doesn't exist."""
        from src.core.ingestion import load_pdf_documents

        result = load_pdf_documents("/nonexistent/path")
        assert result == []

    def test_returns_empty_list_when_no_pdfs(self, tmp_path):
        """Returns empty list when directory has no PDF files."""
        from src.core.ingestion import load_pdf_documents

        result = load_pdf_documents(str(tmp_path))
        assert result == []

    def test_loads_pdfs_with_metadata(self, tmp_path):
        """Loads PDFs and adds source_type metadata."""
        # Create a minimal valid PDF
        pdf_content = b"""%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
206
%%EOF"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(pdf_content)

        from src.core.ingestion import load_pdf_documents

        result = load_pdf_documents(str(tmp_path))

        assert len(result) >= 1
        for doc in result:
            assert doc.metadata["source_type"] == "pdf"
            assert "file_name" in doc.metadata

    def test_metadata_includes_file_name(self, tmp_path):
        """Each document has file_name in metadata."""
        pdf_content = b"""%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
206
%%EOF"""
        (tmp_path / "myfile.pdf").write_bytes(pdf_content)

        from src.core.ingestion import load_pdf_documents

        result = load_pdf_documents(str(tmp_path))

        assert len(result) >= 1
        assert result[0].metadata["file_name"] == "myfile.pdf"

    @patch("src.core.ingestion.SimpleDirectoryReader")
    def test_handles_read_error_gracefully(self, mock_reader, tmp_path):
        """Continues gracefully when reader raises an exception."""
        # Create a PDF so the glob check passes
        (tmp_path / "bad.pdf").write_bytes(b"%PDF-1.0 corrupted")
        mock_reader.side_effect = Exception("Read error")

        from src.core.ingestion import load_pdf_documents

        result = load_pdf_documents(str(tmp_path))
        assert result == []


class TestLoadWebDocuments:
    """Test load_web_documents() function."""

    def test_returns_empty_list_when_file_missing(self):
        """Returns empty list when URLs file doesn't exist."""
        from src.core.ingestion import load_web_documents

        result = load_web_documents("/nonexistent/urls.txt")
        assert result == []

    def test_returns_empty_list_when_file_has_only_comments(self, tmp_path):
        """Returns empty list when file has only comments."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("# This is a comment\n# Another comment\n")

        from src.core.ingestion import load_web_documents

        result = load_web_documents(str(urls_file))
        assert result == []

    @patch("src.core.ingestion.trafilatura")
    def test_loads_web_pages_with_metadata(self, mock_traf, tmp_path):
        """Loads web pages and adds source_type metadata."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://example.com/page1\n")

        mock_traf.fetch_url.return_value = "<html>content</html>"
        mock_traf.extract.return_value = "Extracted content from page"

        from src.core.ingestion import load_web_documents

        result = load_web_documents(str(urls_file))

        assert len(result) == 1
        assert result[0].text == "Extracted content from page"
        assert result[0].metadata["source_type"] == "web"
        assert result[0].metadata["source_url"] == "https://example.com/page1"

    @patch("src.core.ingestion.trafilatura")
    def test_skips_unreachable_urls(self, mock_traf, tmp_path):
        """Continues processing when a URL is unreachable."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://bad.com\nhttps://good.com\n")

        mock_traf.fetch_url.side_effect = [None, "<html>good</html>"]
        mock_traf.extract.return_value = "Good content"

        from src.core.ingestion import load_web_documents

        result = load_web_documents(str(urls_file))

        assert len(result) == 1
        assert result[0].metadata["source_url"] == "https://good.com"

    @patch("src.core.ingestion.trafilatura")
    def test_skips_urls_with_no_content(self, mock_traf, tmp_path):
        """Skips URLs where trafilatura extracts no content."""
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://empty.com\n")

        mock_traf.fetch_url.return_value = "<html></html>"
        mock_traf.extract.return_value = None

        from src.core.ingestion import load_web_documents

        result = load_web_documents(str(urls_file))
        assert result == []


class TestRunIngestionPipeline:
    """Test run_ingestion_pipeline() function."""

    def test_returns_zero_for_empty_documents(self):
        """Returns 0 when given empty document list."""
        from src.core.ingestion import run_ingestion_pipeline

        result = run_ingestion_pipeline([])
        assert result == 0

    @patch("src.core.vector_store.QdrantClient")
    @patch("src.config.providers.QdrantClient")
    @patch("src.config.providers.AsyncQdrantClient")
    @patch("llama_index.core.ingestion.IngestionPipeline.run")
    def test_runs_pipeline_with_documents(self, mock_run, mock_async, mock_sync, mock_vs_client, monkeypatch):
        """Pipeline runs and returns chunk count."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from llama_index.core import Document

        from src.config.settings import get_settings

        get_settings.cache_clear()

        # Mock the pipeline run to return 3 nodes
        mock_run.return_value = [MagicMock(), MagicMock(), MagicMock()]
        # Mock Qdrant clients
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_sync.return_value = mock_client
        mock_vs_client.return_value = mock_client
        mock_async.return_value = MagicMock()

        from src.core.ingestion import run_ingestion_pipeline

        docs = [Document(text="test content", metadata={"source_type": "pdf"})]
        result = run_ingestion_pipeline(docs)

        assert result == 3
        mock_run.assert_called_once()
