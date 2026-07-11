"""Ingestion pipeline — runs adapters to populate raw/."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from llmwiki.adapters import _ensure_all_loaded, _REGISTRY
from llmwiki.state import BuildState

logger = logging.getLogger(__name__)


def ingest_source(
    source_path: Path,
    raw_dir: Path,
    state_path: Path,
    config: dict,
    adapter_name: str | None = None,
) -> dict:
    """Ingest files from a single source directory into raw/.

    Returns summary dict with added/modified/unchanged/skipped/errors counts.
    """
    _ensure_all_loaded()
    state = BuildState(state_path)

    counts = {"added": 0, "modified": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    exclude = config.get("exclude", [])

    for name, adapter_cls in _REGISTRY.items():
        if adapter_name and name != adapter_name:
            continue
        adapter = adapter_cls()
        files = adapter.discover(source_path, exclude=exclude)

        for fpath in files:
            src_key = str(fpath)

            # Compute hash
            try:
                content = fpath.read_bytes()
            except OSError:
                counts["errors"] += 1
                continue
            content_hash = hashlib.sha256(content).hexdigest()[:16]

            classification = state.classify(src_key, content_hash)
            if classification == "unchanged":
                counts["unchanged"] += 1
                continue

            # Extract pages
            try:
                pages = adapter.extract(fpath, config)
            except Exception as e:
                logger.warning("Failed to process %s: %s", fpath, e)
                counts["errors"] += 1
                continue

            # Write to raw/
            out_paths = []
            for page in pages:
                out_path = raw_dir / page.category / f"{page.slug.split('/')[-1]}.md"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(page.to_markdown(), encoding="utf-8")
                out_paths.append(str(out_path))

            state.record_file(src_key, content_hash, ",".join(out_paths) if out_paths else "")
            # Map "new" → "added" for the counts dict
            if classification == "new":
                counts["added"] += 1
            else:
                counts[classification] += 1

    state.save()
    return counts


def ingest_pdfs(
    pdf_paths: list[dict],
    raw_dir: Path,
    state_path: Path,
) -> dict:
    """Ingest PDF files from configured paths."""
    _ensure_all_loaded()
    from llmwiki.adapters.pdf_adapter import PDFAdapter

    state = BuildState(state_path)
    adapter = PDFAdapter()
    counts = {"added": 0, "modified": 0, "unchanged": 0, "errors": 0}

    for pdf_source in pdf_paths:
        src_path = Path(pdf_source["path"])
        label = pdf_source.get("label", "docs")

        if src_path.is_file():
            pdf_files = [src_path]
        elif src_path.is_dir():
            pdf_files = sorted(src_path.rglob("*.pdf"))
        else:
            continue

        for fpath in pdf_files:
            src_key = str(fpath)
            try:
                content_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()[:16]
            except OSError:
                counts["errors"] += 1
                continue

            classification = state.classify(src_key, content_hash)
            if classification == "unchanged":
                counts["unchanged"] += 1
                continue

            try:
                pages = adapter.extract(fpath, {"label": label})
            except Exception as e:
                logger.warning("Failed to process %s: %s", fpath, e)
                counts["errors"] += 1
                continue

            out_paths = []
            for page in pages:
                out_path = raw_dir / page.category / f"{page.slug.split('/')[-1]}.md"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(page.to_markdown(), encoding="utf-8")
                out_paths.append(str(out_path))

            state.record_file(src_key, content_hash, ",".join(out_paths) if out_paths else "")
            if classification == "new":
                counts["added"] += 1
            else:
                counts[classification] += 1

    state.save()
    return counts


def ingest_all(
    config: dict,
    raw_dir: Path,
    state_path: Path,
) -> dict:
    """Run full ingestion from all configured sources."""
    totals = {"total_added": 0, "total_modified": 0, "total_unchanged": 0, "total_errors": 0}

    # Ingest codebase sources
    for source in config.get("sources", []):
        src_path = Path(source["path"])
        if src_path.exists():
            result = ingest_source(src_path, raw_dir, state_path, source)
            totals["total_added"] += result["added"]
            totals["total_modified"] += result["modified"]
            totals["total_unchanged"] += result["unchanged"]
            totals["total_errors"] += result.get("errors", 0)

    # Ingest PDFs
    pdf_sources = config.get("pdf_sources", [])
    if pdf_sources:
        result = ingest_pdfs(pdf_sources, raw_dir, state_path)
        totals["total_added"] += result["added"]
        totals["total_modified"] += result["modified"]
        totals["total_unchanged"] += result["unchanged"]
        totals["total_errors"] += result.get("errors", 0)

    return totals
