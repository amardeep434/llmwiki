"""Ingestion pipeline — runs adapters to populate raw/."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from llmwiki.adapters import _ensure_all_loaded, _REGISTRY
from llmwiki.redact import compile_redact_patterns, redact_text
from llmwiki.state import BuildState

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"%%([A-Z_][A-Z0-9_]+)%%")


def ingest_source(
    source_path: Path,
    raw_dir: Path,
    state_path: Path,
    config: dict,
    adapter_name: str | None = None,
    security: dict | None = None,
) -> dict:
    """Ingest files from a single source directory into raw/.

    Returns summary dict with added/modified/unchanged/skipped/errors counts,
    plus ``redacted`` (secrets scrubbed) and ``redacted_pages`` (pages touched).

    ``security`` carries the top-level ``security`` config block (redaction is
    per-project, not per-source); it is threaded in separately because
    ``config`` here is the per-source dict.
    """
    _ensure_all_loaded()
    state = BuildState(state_path)

    security = security or {}
    redact_enabled = security.get("redact", True)
    extra_patterns = compile_redact_patterns(security.get("redact_patterns"))

    counts = {
        "added": 0, "modified": 0, "unchanged": 0, "skipped": 0, "errors": 0,
        "redacted": 0, "redacted_pages": 0,
    }
    exclude = config.get("exclude", [])

    # Raw output paths written during THIS run. make_slug already guarantees
    # unique page ids, but the raw filename is only the slug's last segment
    # under its category dir, so two distinct ids can still target one file
    # (e.g. src/a/utils.py and src/b/utils.py → raw/<cat>/utils.md). If that
    # happens, disambiguate the second file rather than silently overwrite.
    written_paths: set[str] = set()

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

            # BeanShell-in-XML extraction is a SailPoint IIQ idiom; keep it
            # opt-in so generic XML sources don't grow bogus script pages.
            adapter_config = dict(config)
            # Give adapters the source root so make_slug can derive path-aware,
            # collision-free page ids (see adapters.base.make_slug).
            adapter_config["_source_root"] = source_path
            try:
                pages = adapter.extract(fpath, adapter_config)
            except Exception as e:
                logger.warning("Failed to process %s: %s", fpath, e)
                counts["errors"] += 1
                continue

            # Redact secrets from each page body BEFORE it is written to raw/,
            # so nothing sensitive ever lands on disk or flows into the DB,
            # search index, or exports downstream.
            if redact_enabled:
                for page in pages:
                    clean, findings = redact_text(page.body, extra_patterns=extra_patterns)
                    if findings:
                        page.body = clean
                        page.compute_hash()
                        counts["redacted"] += sum(f["count"] for f in findings)
                        counts["redacted_pages"] += 1

            # Write to raw/
            out_paths = []
            for page in pages:
                out_path = raw_dir / page.category / f"{page.slug.split('/')[-1]}.md"
                if str(out_path) in written_paths:
                    prefix = hashlib.sha256(page.body.encode("utf-8")).hexdigest()[:8]
                    out_path = out_path.with_name(f"{out_path.stem}-{prefix}.md")
                    logger.warning(
                        "Slug collision: raw path already written this run for "
                        "page id %r; writing disambiguated file %s",
                        page.slug, out_path,
                    )
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(page.to_markdown(), encoding="utf-8")
                written_paths.add(str(out_path))
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
    totals = {
        "total_added": 0, "total_modified": 0, "total_unchanged": 0,
        "total_errors": 0, "total_redacted": 0, "total_redacted_pages": 0,
        "total_removed": 0,
    }
    security = config.get("security", {})

    # Ingest codebase sources
    for source in config.get("sources", []):
        src_path = Path(source["path"])
        if src_path.exists():
            result = ingest_source(src_path, raw_dir, state_path, source, security=security)
            totals["total_added"] += result["added"]
            totals["total_modified"] += result["modified"]
            totals["total_unchanged"] += result["unchanged"]
            totals["total_errors"] += result.get("errors", 0)
            totals["total_redacted"] += result.get("redacted", 0)
            totals["total_redacted_pages"] += result.get("redacted_pages", 0)

    # Ingest PDFs
    pdf_sources = config.get("pdf_sources", [])
    if pdf_sources:
        result = ingest_pdfs(pdf_sources, raw_dir, state_path)
        totals["total_added"] += result["added"]
        totals["total_modified"] += result["modified"]
        totals["total_unchanged"] += result["unchanged"]
        totals["total_errors"] += result.get("errors", 0)

    # Prune sources that no longer exist. Only safe in ingest_all: this is a
    # full run that discovered every source, so a recorded file now absent is
    # genuinely deleted/renamed (a filtered --adapter run sees a subset and
    # must never prune). Removing the recorded raw output(s) and the state
    # entry keeps deletions from lingering in raw/, the DB, and exports.
    totals["total_removed"] = _prune_deleted(config, state_path)

    # Generate token registry from all raw pages
    _generate_token_registry(raw_dir)

    return totals


def _prune_deleted(config: dict, state_path: Path) -> int:
    """Delete raw outputs and state entries for sources that vanished.

    Returns the number of source entries removed. Uses the same discovery
    logic as ingestion (via freshness._discover_current_files) so the current
    file set exactly matches what the adapters would ingest today.
    """
    if not state_path.exists():
        return 0

    from llmwiki.freshness import _discover_current_files

    state = BuildState(state_path)
    current_files = _discover_current_files(config)
    deleted = state.detect_deleted(current_files)
    if not deleted:
        return 0

    for src_key in deleted:
        entry = state.files.get(src_key, {})
        raw_path = entry.get("raw_path", "")
        for out_path in (raw_path.split(",") if raw_path else []):
            if not out_path:
                continue
            try:
                Path(out_path).unlink()
            except OSError:
                pass
        state.files.pop(src_key, None)

    state.save()
    return len(deleted)


def _generate_token_registry(raw_dir: Path) -> None:
    """Scan all raw pages for %%TOKEN%% patterns and create a token registry."""
    tokens: dict[str, list[str]] = {}  # token_name -> [source_files]

    for md_file in raw_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        found = _TOKEN_RE.findall(content)
        if found:
            # Use the filename stem as page title
            page_title = md_file.stem.replace("-", " ").replace("_", " ")
            for token in found:
                tokens.setdefault(token, []).append(page_title)

    if not tokens:
        return

    # Create token registry page
    body_lines = [f"# Token Registry\n\n{len(tokens)} environment tokens found.\n"]
    for token_name in sorted(tokens.keys()):
        sources = tokens[token_name]
        body_lines.append(f"## %%{token_name}%%\n")
        body_lines.append(f"Used in {len(sources)} files:\n")
        for src in sorted(set(sources))[:10]:
            body_lines.append(f"- [[{src}]]")
        body_lines.append("")

    from llmwiki.adapters.base import WikiPage
    page = WikiPage(
        slug="tokens/registry",
        title="Token Registry",
        category="tokens",
        source_path="(generated)",
        body="\n".join(body_lines),
        tags=["tokens", "configuration"],
    )
    page.compute_hash()
    out_path = raw_dir / "tokens" / "registry.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page.to_markdown(), encoding="utf-8")
