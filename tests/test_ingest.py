"""Tests for the ingestion pipeline."""

from pathlib import Path
from llmwiki.ingest import ingest_source, ingest_all
from llmwiki.config import create_default_config


class TestIngest:
    def test_ingest_source_creates_raw_files(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "Main.java").write_text("public class Main {}")
        (src / "README.md").write_text("# Project\n\nDescription.")
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        result = ingest_source(
            source_path=src, raw_dir=raw_dir,
            state_path=tmp_path / ".llmwiki-state.json", config={},
        )
        assert result["added"] > 0
        md_files = list(raw_dir.rglob("*.md"))
        assert len(md_files) >= 1

    def test_ingest_incremental_skips_unchanged(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "Main.java").write_text("public class Main {}")
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        state_path = tmp_path / ".llmwiki-state.json"
        r1 = ingest_source(src, raw_dir, state_path, {})
        assert r1["added"] >= 1
        r2 = ingest_source(src, raw_dir, state_path, {})
        assert r2["added"] == 0
        assert r2["unchanged"] >= 1

    def test_ingest_all(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "app.py").write_text("def main(): pass")
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        config = create_default_config("Test", str(src))
        result = ingest_all(config, raw_dir, tmp_path / ".llmwiki-state.json")
        assert result["total_added"] >= 1


def test_pdf_inside_source_dir_keeps_configured_label(tmp_path, monkeypatch):
    """Dogfood finding: a PDF under a source dir was ingested by the source
    scan (default label) before ingest_pdfs could apply the configured label.
    PDF sources must be ingested first so their label wins."""
    from llmwiki.ingest import ingest_all
    from llmwiki.adapters.base import WikiPage

    src = tmp_path / "proj"
    (src / "docs-pdf").mkdir(parents=True)
    pdf = src / "docs-pdf" / "guide.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    raw = tmp_path / "raw"; raw.mkdir()

    def fake_extract(self, path, config):
        page = WikiPage(
            slug=f"{config.get('label', 'docs')}/guide", title="Guide",
            category=config.get("label", "docs"), source_path=str(path),
            body="guide body",
        )
        page.compute_hash()
        return [page]

    from llmwiki.adapters import pdf_adapter
    monkeypatch.setattr(pdf_adapter.PDFAdapter, "extract", fake_extract)

    config = {
        "sources": [{"path": str(src), "exclude": []}],
        "pdf_sources": [{"path": str(src / "docs-pdf"), "label": "papers"}],
    }
    ingest_all(config, raw, tmp_path / "state.json")
    assert (raw / "papers" / "guide.md").exists()
    assert not (raw / "docs" / "guide.md").exists()


def test_token_registry_uses_plain_names_not_wikilinks(tmp_path):
    """Phase V: registry [[wikilinks]] produced 784 broken-link lint errors."""
    from llmwiki.ingest import _generate_token_registry
    raw = tmp_path / "raw"
    (raw / "config").mkdir(parents=True)
    (raw / "config" / "app.md").write_text(
        "name %%SOME_TOKEN%% here", encoding="utf-8")
    _generate_token_registry(raw)
    registry = (raw / "tokens" / "registry.md").read_text(encoding="utf-8")
    assert "[[" not in registry
    assert "`app`" in registry
