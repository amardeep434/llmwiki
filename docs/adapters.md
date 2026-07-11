# Adapters

Adapters are the ingestion layer that converts source files into standardized `WikiPage` objects. LLMWiki ships with 6 built-in adapters and supports custom adapters.

---

## Built-In Adapters

| Adapter | Name | File Extensions | Description |
|---------|------|-----------------|-------------|
| Source Code | `source-code` | 30+ extensions (see below) | Extracts structure, docs, imports, classes, methods/functions, and `method:*` tags |
| XML | `xml` | `.xml`, `.xsl`, `.xslt`, `.xsd`, `.wsdl` | Parses XML structure, extracts inline scripts |
| PDF | `pdf` | `.pdf` | Converts PDFs to markdown via `pymupdf` with font-based heading detection |
| Markdown | `markdown` | `.md`, `.mdx`, `.rst` | Pass-through with frontmatter extraction |
| Config | `config` | `.json`, `.yaml`, `.yml`, `.toml`, `.properties`, `.ini`, `.env`, `.cfg` | Documents configuration files |
| Generic | `generic` | *(any text file)* | Registered text adapter that wraps files in code blocks; not auto-discovered during normal ingest |

---

## Language Support Matrix (Source Code Adapter)

The source-code adapter handles 30+ languages via file extension mapping:

| Language | Extensions |
|----------|-----------|
| Java | `.java` |
| Python | `.py` |
| JavaScript | `.js`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |
| Go | `.go` |
| Rust | `.rs` |
| C# | `.cs` |
| C | `.c`, `.h` |
| C++ | `.cpp`, `.hpp` |
| Ruby | `.rb` |
| Kotlin | `.kt` |
| Swift | `.swift` |
| Scala | `.scala` |
| PHP | `.php` |
| Shell | `.sh`, `.bash`, `.zsh` |
| SQL | `.sql` |
| R | `.r` |
| Lua | `.lua` |
| Perl | `.pl` |
| Elixir | `.ex`, `.exs` |
| Haskell | `.hs` |
| Clojure | `.clj` |
| Dart | `.dart` |
| Groovy | `.groovy` |
| Objective-C | `.m` |

### Language-Specific Parsing

The source-code adapter applies specialized parsing for certain languages:

**Java:**
- Extracts Javadoc comments as page overviews
- Parses `import` statements as cross-references
- Lists classes, interfaces, enums, and public methods
- Detects package for category assignment

**Python:**
- Extracts module and class docstrings
- Parses `import` and `from ... import` as cross-references
- Lists classes (with first-line docstrings) and public functions
- Categorizes by directory structure

**All other languages:**
- Extracts leading comments (line comments `//`, `#`, `--` and block comments `/* */`)
- Categorizes by parent directory structure

For Java, Python, JavaScript, TypeScript, Go, Rust, C#, Ruby, Kotlin, Swift, Scala, PHP, Bash, Lua, Perl, Elixir, Haskell, Dart, and Groovy, the adapter also extracts method/function names and adds up to 20 `method:<name>` tags per page.

All extracted pages include a collapsible `<details>` block with the full source code.

---

## XML Adapter Details

The XML adapter provides specialized handling for:

- **Generic XML**: extracts element structure and attributes
- **Inline scripts**: detects `<Source>`, `<Script>`, `<Code>` elements (common in SailPoint IIQ and similar platforms) and extracts them as separate wiki pages
- **Cross-references**: extracts `name="..."` attributes and Java imports within BeanShell code blocks

---

## PDF Adapter Details

PDF conversion uses `pymupdf` (the PyMuPDF library, ≥1.24.0) with custom structured extraction:

- **Font-based heading detection**: analyzes font sizes across the document to determine heading hierarchy (H1–H4) based on relative size ranking
- **Table extraction**: uses `page.find_tables()` to detect and convert tables into proper markdown table syntax
- **Sub-bullet glyph handling**: detects Wingdings bullet characters and Unicode glyph markers for nested list items
- **Image extraction**: extracts embedded images to an `assets/` directory alongside the markdown output
- **Header/footer stripping**: identifies recurring text at consistent top/bottom positions across pages and removes it
- **Copyright page detection**: heuristically identifies and skips copyright/disclaimer pages
- **Code block detection**: identifies monospace font spans and wraps them in code formatting
- Each PDF produces one wiki page
- Configure via `pdf_sources` in `llmwiki.json`

---

## Adapter Processing Order

During ingestion, LLMWiki runs the registered adapters whose `discover()` methods return files. Each matching file is then passed to `extract()`:

```
For each source in config.sources:
    For each registered adapter:
        files = adapter.discover(source_path, exclude=...)
        For each file:
            hash = SHA-256(file_content)
            if hash unchanged → skip
            pages = adapter.extract(file, config)
            write pages to raw/{category}/{slug}.md
```

The generic adapter has no predefined extensions and returns no files from `discover()`, so it is not auto-discovered during normal CLI ingestion.

---

## Writing a Custom Adapter

### 1. Create the Adapter

Create a new file in `llmwiki/adapters/`:

```python
"""Custom adapter for .xyz files."""

from pathlib import Path
from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


@register
class XyzAdapter(BaseAdapter):
    name = "xyz"
    extensions = [".xyz"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".xyz"

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        content = path.read_text(encoding="utf-8", errors="replace")

        page = WikiPage(
            slug=f"xyz/{path.stem}",
            title=path.stem,
            category="xyz",
            source_path=str(path),
            body=f"## {path.stem}\n\n```\n{content}\n```",
            language="xyz",
            tags=["xyz"],
            references=[],  # Extract cross-refs if applicable
        )
        page.compute_hash()
        return [page]
```

### 2. Register the Module

Add your module name to the `_names` list in `llmwiki/adapters/__init__.py`:

```python
_names = [
    "config_adapter", "generic_adapter", "markdown_adapter",
    "pdf_adapter", "source_code", "xml_adapter",
    "xyz_adapter",  # ← your adapter
]
```

### 3. Test

```bash
llmwiki init --source /path/with/xyz/files
llmwiki ingest
```

`llmwiki ingest --adapter ...` is accepted by the CLI parser, but adapter-scoped ingestion is not currently wired up in the standard command flow.

---

## BaseAdapter API

| Method | Signature | Description |
|--------|-----------|-------------|
| `can_handle` | `(path: Path) → bool` | Return `True` if this adapter should process the file |
| `extract` | `(path: Path, config: dict) → list[WikiPage]` | Convert file into one or more `WikiPage` objects |
| `discover` | `(root: Path, exclude: list[str]) → list[Path]` | Find all matching files under `root` (default: glob by `extensions`) |

### WikiPage Fields

| Field | Type | Description |
|-------|------|-------------|
| `slug` | `str` | Unique identifier, typically `category/name` |
| `title` | `str` | Display title |
| `category` | `str` | Category for grouping (e.g., package path, `"docs"`) |
| `source_path` | `str` | Absolute path to the original source file |
| `body` | `str` | Markdown body content |
| `language` | `str` | Programming language (for syntax highlighting) |
| `tags` | `list[str]` | Tags for search and clustering |
| `references` | `list[str]` | Outbound cross-references (slugs or identifiers) |
| `metadata` | `dict` | Arbitrary metadata |
| `content_hash` | `str` | SHA-256 hash (first 16 hex chars) for change detection |
