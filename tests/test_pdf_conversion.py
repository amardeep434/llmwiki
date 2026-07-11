"""Tests for structured PDF-to-markdown conversion using real SailPoint PDFs."""

import pytest
from pathlib import Path
from llmwiki.adapters.pdf_adapter import _convert_pdf_structured


SAMPLE_PDF = Path("/home/amardeep/Downloads/identityiq-8.5/doc/8.5_IdentityIQ_Getting_Started.pdf")
CONNECTOR_PDF = Path("/home/amardeep/Downloads/8.5p1 Connector and Integration Guides/SailPoint Active Directory Connector Guide.pdf")
PROVISIONING_PDF = Path("/home/amardeep/Downloads/identityiq-8.5/doc/8.5_IdentityIQ_Provisioning.pdf")


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="Test PDF not available")
class TestPDFConversion:
    def test_has_headings(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        assert "# " in result or "## " in result

    def test_has_content(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        assert len(result) > 1000

    def test_no_raw_dump(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        # Should NOT have the "Page N" markers from raw extraction
        assert "*Page 2*" not in result

    def test_strips_copyright(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        lines = result.split("\n")[:10]
        assert not any("Copyright" in line for line in lines)

    def test_bullet_lists(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        assert "\n- " in result

    def test_no_excessive_blank_lines(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        assert "\n\n\n\n" not in result

    def test_paragraphs_joined(self, tmp_path):
        result = _convert_pdf_structured(SAMPLE_PDF, tmp_path / "assets")
        # Body paragraphs should have reasonable line lengths (joined)
        lines = [l for l in result.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("-")]
        if lines:
            avg_len = sum(len(l) for l in lines[:50]) / min(50, len(lines))
            assert avg_len > 40, f"Average line length {avg_len} too short — paragraphs not joined"


@pytest.mark.skipif(not CONNECTOR_PDF.exists(), reason="Connector PDF not available")
class TestPDFTables:
    def test_has_tables(self, tmp_path):
        result = _convert_pdf_structured(CONNECTOR_PDF, tmp_path / "assets")
        assert "|" in result and "---" in result

    def test_table_structure(self, tmp_path):
        result = _convert_pdf_structured(CONNECTOR_PDF, tmp_path / "assets")
        # Should have proper pipe table format
        lines = result.split("\n")
        table_lines = [l for l in lines if l.startswith("|")]
        assert len(table_lines) > 3, "Expected multiple table rows"


@pytest.mark.skipif(not PROVISIONING_PDF.exists(), reason="Provisioning PDF not available")
class TestPDFProvisioning:
    def test_has_headings(self, tmp_path):
        result = _convert_pdf_structured(PROVISIONING_PDF, tmp_path / "assets")
        heading_count = len(re.findall(r"^#{1,4} .+", result, re.MULTILINE))
        assert heading_count >= 5, f"Only {heading_count} headings found"

    def test_has_structure(self, tmp_path):
        result = _convert_pdf_structured(PROVISIONING_PDF, tmp_path / "assets")
        # Should have mix of headings, paragraphs, and lists
        assert "## " in result or "### " in result
        assert "\n- " in result


import re
