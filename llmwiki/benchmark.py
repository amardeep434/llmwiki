"""Token efficiency benchmark — realistic agent baseline vs wiki search.

Methodology (printed with every report so the numbers are auditable):

Baseline ("without wiki") simulates how a modern coding agent actually
works: it greps for the query terms, ranks files by how many distinct
terms they contain, and fully reads the top TOP_K_FILES matches. It does
NOT assume the agent reads every file containing any keyword — that
strawman produced fantasy savings numbers and is exactly the kind of
claim that gets a tool dismissed.

Wiki side simulates the documented agent flow: `llmwiki search --agent`
(result list) plus one `llmwiki get` of the top hit (full page,
source-stripped).

Token counts are len/4 approximations; treat results as estimates, not
billing math.
"""

from __future__ import annotations

from pathlib import Path

TOP_K_FILES = 5
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "who", "why",
    "with", "work", "works",
}
SKIP_EXTS = {".pyc", ".class", ".o", ".so", ".dll", ".jar", ".war",
             ".png", ".jpg", ".gif", ".ico", ".svg", ".zip", ".tar", ".gz",
             ".db", ".sqlite"}
# Never count generated/vendored trees in the baseline — inflating the
# raw side with the wiki's own output would fake the savings numbers.
SKIP_DIRS = {".llmwiki", ".git", "node_modules", "__pycache__", ".venv",
             "venv", "build", "dist"}


def count_tokens(text: str) -> int:
    """Approximate token count (len/4 — no external deps)."""
    return max(1, len(text) // 4)


def _query_terms(query: str) -> list[str]:
    terms = [t for t in query.lower().split() if t not in STOPWORDS]
    return terms or query.lower().split()


def count_raw_tokens(source_dirs: list[Path], query: str,
                     top_k: int = TOP_K_FILES) -> tuple[int, int]:
    """Tokens a grep-then-read agent would spend answering the query.

    Ranks files by number of distinct query terms they contain, then
    sums tokens of the top_k best matches (the files an agent would
    actually open). Returns (total_tokens, files_read).
    """
    terms = _query_terms(query)
    scored: list[tuple[int, int, str]] = []  # (term_hits, tokens, path)

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for f in source_dir.rglob("*"):
            if not f.is_file() or f.suffix.lower() in SKIP_EXTS:
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue
            content_lower = content.lower()
            hits = sum(1 for t in terms if t in content_lower)
            if hits:
                scored.append((hits, count_tokens(content), str(f)))

    scored.sort(key=lambda x: (-x[0], -x[1]))
    top = scored[:top_k]
    return sum(tokens for _, tokens, _ in top), len(top)


def count_wiki_tokens(site_dir: Path, query: str) -> tuple[int, int]:
    """Tokens of the documented wiki agent flow: search --agent + get top hit.

    Returns (total_tokens, pages_matched). Requires llmwiki.db; falls
    back to (0, 0) when the index hasn't been built.
    """
    from llmwiki.search import (
        search_pages, get_page,
        format_results_agent, format_page_for_agent,
    )

    db_path = site_dir / "llmwiki.db"
    if not db_path.exists():
        return 0, 0

    results = search_pages(db_path, query, limit=10)
    if not results:
        return 0, 0

    total = count_tokens(format_results_agent(results))
    top = get_page(db_path, results[0]["id"])
    if top:
        total += count_tokens(format_page_for_agent(top))
    return total, len(results)


def run_benchmark(query: str, source_dirs: list[Path], site_dir: Path) -> dict:
    """Run full benchmark and return results dict."""
    raw_tokens, raw_files = count_raw_tokens(source_dirs, query)
    wiki_tokens, wiki_pages = count_wiki_tokens(site_dir, query)
    savings = raw_tokens - wiki_tokens
    pct = (savings / raw_tokens * 100) if raw_tokens > 0 else 0
    return {
        "query": query,
        "raw_tokens": raw_tokens,
        "raw_files": raw_files,
        "wiki_tokens": wiki_tokens,
        "wiki_pages": wiki_pages,
        "savings_tokens": savings,
        "savings_pct": round(pct, 1),
        "top_k": TOP_K_FILES,
    }


def format_benchmark_report(result: dict) -> str:
    """Format benchmark result as a report, methodology included."""
    q = result["query"]
    raw = result["raw_tokens"]
    raw_f = result["raw_files"]
    wiki = result["wiki_tokens"]
    wiki_p = result["wiki_pages"]
    savings = result["savings_tokens"]
    pct = result["savings_pct"]
    top_k = result.get("top_k", TOP_K_FILES)

    if wiki == 0:
        verdict = "  No wiki results — build the index first (`llmwiki all`).\n"
    elif savings > 0:
        verdict = f"  Estimated savings: {savings:,} tokens ({pct}%)\n"
    else:
        verdict = (
            f"  No savings on this query ({abs(savings):,} tokens MORE via wiki).\n"
            "  Reading the files directly is cheaper here — that's a valid outcome.\n"
        )

    return (
        "\nToken Efficiency Estimate\n"
        "─────────────────────────\n"
        f"  Query: \"{q}\"\n\n"
        f"  Baseline (grep + read top {top_k} matching files, like a coding agent):\n"
        f"    Files read: {raw_f}   Tokens: {raw:,}\n\n"
        "  Wiki flow (search --agent + get top page):\n"
        f"    Pages matched: {wiki_p}   Tokens: {wiki:,}\n\n"
        f"{verdict}"
        "\n  Methodology: baseline ranks files by distinct query-term hits and\n"
        f"  reads the {top_k} best matches in full; it does NOT assume an agent\n"
        "  reads every keyword-matching file. Token counts are len/4 estimates.\n"
    )
