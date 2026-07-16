"""Token efficiency benchmark — compare raw file reading vs wiki search."""

from __future__ import annotations

import json
from pathlib import Path


def count_tokens(text: str) -> int:
    """Approximate token count (len/4 — no external deps)."""
    return max(1, len(text) // 4)


def count_raw_tokens(source_dirs: list[Path], query: str) -> tuple[int, int]:
    """Count tokens of all source files matching a query via keyword grep.
    
    Returns (total_tokens, files_matched).
    """
    keywords = query.lower().split()
    total = 0
    matched = 0
    skip_exts = {".pyc", ".class", ".o", ".so", ".dll", ".jar", ".war",
                 ".png", ".jpg", ".gif", ".ico", ".svg", ".zip", ".tar", ".gz"}
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for f in source_dir.rglob("*"):
            if not f.is_file() or f.suffix.lower() in skip_exts:
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue
            content_lower = content.lower()
            if any(kw in content_lower for kw in keywords):
                total += count_tokens(content)
                matched += 1
    return total, matched


def count_wiki_tokens(wiki_dir: Path, query: str) -> tuple[int, int]:
    """Count tokens of wiki search results for the same query.
    
    Returns (total_tokens, pages_matched).
    """
    idx_path = wiki_dir / "search-index.json"
    if not idx_path.exists():
        return 0, 0
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = data.get("entries", data if isinstance(data, list) else [])
    keywords = query.lower().split()
    total = 0
    matched = 0
    for entry in entries:
        text = f"{entry.get('title', '')} {entry.get('body', '')} {' '.join(entry.get('tags', []))}".lower()
        if any(kw in text for kw in keywords):
            result_text = f"{entry.get('title', '')}\n{entry.get('category', '')}\n{entry.get('body', '')}"
            total += count_tokens(result_text)
            matched += 1
    return total, matched


def run_benchmark(query: str, source_dirs: list[Path], wiki_dir: Path) -> dict:
    """Run full benchmark and return results dict."""
    raw_tokens, raw_files = count_raw_tokens(source_dirs, query)
    wiki_tokens, wiki_pages = count_wiki_tokens(wiki_dir, query)
    savings = raw_tokens - wiki_tokens if raw_tokens > wiki_tokens else 0
    pct = (savings / raw_tokens * 100) if raw_tokens > 0 else 0
    cost_saved = savings * 0.000005  # ~$5/1M tokens GPT-4 input estimate
    return {
        "query": query,
        "raw_tokens": raw_tokens,
        "raw_files": raw_files,
        "wiki_tokens": wiki_tokens,
        "wiki_pages": wiki_pages,
        "savings_tokens": savings,
        "savings_pct": round(pct, 1),
        "cost_saved_per_query": round(cost_saved, 6),
    }


def format_benchmark_report(result: dict) -> str:
    """Format benchmark result as a visual report."""
    q = result["query"]
    raw = result["raw_tokens"]
    raw_f = result["raw_files"]
    wiki = result["wiki_tokens"]
    wiki_p = result["wiki_pages"]
    savings = result["savings_tokens"]
    pct = result["savings_pct"]
    cost = result["cost_saved_per_query"]
    return (
        "\n"
        "┌──────────────────────────────────────────────────┐\n"
        "│  Token Efficiency Report                         │\n"
        "├──────────────────────────────────────────────────┤\n"
        f"│  Query: \"{q}\"\n"
        "│\n"
        "│  Without LLMWiki (raw file reading):\n"
        f"│    Files matched: {raw_f}\n"
        f"│    Total tokens: {raw:,}\n"
        "│\n"
        "│  With LLMWiki (wiki search):\n"
        f"│    Pages returned: {wiki_p}\n"
        f"│    Total tokens: {wiki:,}\n"
        "│\n"
        "│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"│  Savings: {savings:,} tokens ({pct}%)\n"
        f"│  Est. cost saved: ~${cost:.4f}/query\n"
        "└──────────────────────────────────────────────────┘\n"
    )
