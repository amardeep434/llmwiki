"""Tests for PDF adapter."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from llmwiki.adapters.pdf_adapter import PDFAdapter


class TestPDFAdapter:
    def setup_method(self):
        self.adapter = PDFAdapter()

    def test_can_handle_pdf(self, tmp_path):
        f = tmp_path / "guide.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        assert self.adapter.can_handle(f)

    def test_cannot_handle_txt(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("hello")
        assert not self.adapter.can_handle(f)

    @patch("llmwiki.adapters.pdf_adapter._convert_pdf")
    def test_extract_pdf(self, mock_convert, tmp_path):
        f = tmp_path / "SailPoint Guide.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        mock_convert.return_value = "# Chapter 1\n\nSome content.\n\n# Chapter 2\n\nMore content."
        pages = self.adapter.extract(f, {"label": "guides"})
        assert len(pages) >= 1
        assert pages[0].language == ""
        assert pages[0].tags == ["pdf"]

    def test_slug_from_filename(self):
        slug = self.adapter._make_slug("SailPoint Active Directory Connector Guide.pdf", "connectors")
        assert " " not in slug
        assert slug.islower() or "/" in slug
