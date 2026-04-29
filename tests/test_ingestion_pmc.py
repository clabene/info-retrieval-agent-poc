"""Tests for PMC fetch functions in src/core/ingestion.py."""

from unittest.mock import MagicMock, patch

import pytest


class TestFetchPMCText:
    """Test _fetch_pmc_text() with mocked HTTP calls."""

    @patch("requests.get")
    def test_europe_pmc_success(self, mock_get):
        """Returns text from Europe PMC when API responds successfully."""
        from src.core.ingestion import _fetch_pmc_text

        # Europe PMC returns valid XML
        # Must be >500 chars total for status_code check, and extracted text >200 chars
        body_text = "This is the full text of a research article about muscle training and hydration. " * 10
        xml_response = f"""<?xml version="1.0"?>
        <article>
            <front><article-title>Test Article About Muscle Training</article-title></front>
            <body><p>{body_text}</p></body>
        </article>"""

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = xml_response
        mock_get.return_value = mock_resp

        result = _fetch_pmc_text("PMC7927075")

        assert result is not None
        assert "muscle training" in result
        assert len(result) > 200
        mock_get.assert_called_once_with(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7927075/fullTextXML",
            timeout=15,
        )

    @patch("requests.get")
    def test_europe_pmc_fails_falls_back_to_efetch(self, mock_get):
        """Falls back to NCBI efetch when Europe PMC returns 404."""
        from src.core.ingestion import _fetch_pmc_text

        # First call (Europe PMC) fails, second call (efetch) succeeds
        epmc_resp = MagicMock()
        epmc_resp.status_code = 404
        epmc_resp.text = "Not Found"

        efetch_body = "Article content from NCBI efetch about exercise physiology. " * 5
        efetch_xml = f"""<?xml version="1.0"?>
        <pmc-articleset>
            <article><body><p>{efetch_body}</p></body></article>
        </pmc-articleset>"""
        efetch_resp = MagicMock()
        efetch_resp.status_code = 200
        efetch_resp.text = efetch_xml

        mock_get.side_effect = [epmc_resp, efetch_resp]

        result = _fetch_pmc_text("PMC3418948")

        assert result is not None
        assert "exercise physiology" in result
        assert mock_get.call_count == 2

    @patch("requests.get")
    def test_both_apis_fail_returns_none(self, mock_get):
        """Returns None when both Europe PMC and efetch fail."""
        from src.core.ingestion import _fetch_pmc_text

        # Both calls fail
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.text = "Error"
        mock_get.return_value = fail_resp

        result = _fetch_pmc_text("PMC0000001")

        assert result is None

    @patch("requests.get")
    def test_europe_pmc_network_error_falls_back(self, mock_get):
        """Network exception on Europe PMC triggers efetch fallback."""
        from src.core.ingestion import _fetch_pmc_text

        efetch_body = "Fallback content from efetch with sufficient length. " * 5
        efetch_xml = f"""<?xml version="1.0"?>
        <pmc-articleset><article><body><p>{efetch_body}</p></body></article></pmc-articleset>"""
        efetch_resp = MagicMock()
        efetch_resp.status_code = 200
        efetch_resp.text = efetch_xml

        mock_get.side_effect = [Exception("timeout"), efetch_resp]

        result = _fetch_pmc_text("PMC1234567")

        assert result is not None
        assert mock_get.call_count == 2

    @patch("requests.get")
    def test_europe_pmc_short_response_falls_back(self, mock_get):
        """Falls back when Europe PMC returns a response shorter than 500 chars."""
        from src.core.ingestion import _fetch_pmc_text

        # Short response (< 500 chars) triggers fallback
        short_resp = MagicMock()
        short_resp.status_code = 200
        short_resp.text = "<error>No content</error>"

        efetch_body = "Longer content from efetch that passes the minimum length validation. " * 5
        efetch_xml = f"""<?xml version="1.0"?>
        <pmc-articleset><article><body><p>{efetch_body}</p></body></article></pmc-articleset>"""
        efetch_resp = MagicMock()
        efetch_resp.status_code = 200
        efetch_resp.text = efetch_xml

        mock_get.side_effect = [short_resp, efetch_resp]

        result = _fetch_pmc_text("PMC9999999")

        assert result is not None
        assert mock_get.call_count == 2

    @patch("requests.get")
    def test_efetch_uses_numeric_id(self, mock_get):
        """efetch URL uses numeric ID without PMC prefix."""
        from src.core.ingestion import _fetch_pmc_text

        # Europe PMC fails
        fail_resp = MagicMock()
        fail_resp.status_code = 404
        fail_resp.text = ""

        # efetch also fails (we just want to check the URL)
        efetch_resp = MagicMock()
        efetch_resp.status_code = 404
        efetch_resp.text = ""

        mock_get.side_effect = [fail_resp, efetch_resp]

        _fetch_pmc_text("PMC4698440")

        # Second call should use numeric ID
        efetch_call = mock_get.call_args_list[1]
        assert "id=4698440" in efetch_call[0][0]
        assert "PMC" not in efetch_call[0][0].split("id=")[1]


class TestFetchGenericURL:
    """Test _fetch_generic_url() with mocked trafilatura."""

    @patch("src.core.ingestion.trafilatura")
    def test_successful_extraction(self, mock_traf):
        """Returns extracted text from a web page."""
        from src.core.ingestion import _fetch_generic_url

        mock_traf.fetch_url.return_value = "<html><body>Page content</body></html>"
        mock_traf.extract.return_value = "Extracted page content with useful info"

        result = _fetch_generic_url("https://example.com/article")

        assert result == "Extracted page content with useful info"
        mock_traf.fetch_url.assert_called_once()
        call_args = mock_traf.fetch_url.call_args
        assert call_args[0][0] == "https://example.com/article"

    @patch("src.core.ingestion.trafilatura")
    def test_fetch_returns_none(self, mock_traf):
        """Returns None when fetch_url returns None (unreachable)."""
        from src.core.ingestion import _fetch_generic_url

        mock_traf.fetch_url.return_value = None

        result = _fetch_generic_url("https://unreachable.com")

        assert result is None

    @patch("src.core.ingestion.trafilatura")
    def test_extract_returns_none(self, mock_traf):
        """Returns None when extract returns None (no useful content)."""
        from src.core.ingestion import _fetch_generic_url

        mock_traf.fetch_url.return_value = "<html></html>"
        mock_traf.extract.return_value = None

        result = _fetch_generic_url("https://empty.com")

        assert result is None


class TestLoadWebDocumentsErrorPaths:
    """Test error handling paths in load_web_documents()."""

    @patch("src.core.ingestion._fetch_generic_url")
    def test_exception_during_url_processing_is_caught(self, mock_fetch, tmp_path):
        """Exception during URL processing logs warning and continues."""
        from src.core.ingestion import load_web_documents

        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://bad.com\nhttps://good.com\n")

        # First URL raises, second succeeds
        mock_fetch.side_effect = [Exception("Network error"), "Good content here"]

        result = load_web_documents(str(urls_file))

        # Should have processed the second URL successfully
        assert len(result) == 1
        assert result[0].metadata["source_url"] == "https://good.com"
