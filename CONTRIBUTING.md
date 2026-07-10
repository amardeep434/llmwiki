# Contributing to LLMWiki

Thank you for considering contributing to LLMWiki! This document covers development setup, code style, testing, and PR guidelines.

---

## Development Setup

### Prerequisites

- Python 3.9+
- Git

### Clone and Install

```bash
git clone https://github.com/your-org/llmwiki.git
cd llmwiki
pip install -e ".[dev]"
```

This installs LLMWiki in editable mode along with development dependencies (`pytest`).

### Verify

```bash
llmwiki --version
pytest tests/
```

---

## Project Structure

```
llmwiki/
├── llmwiki/              # Main package
│   ├── __init__.py       # Version and package root
│   ├── __main__.py       # python -m llmwiki entry point
│   ├── cli.py            # CLI dispatcher (argparse)
│   ├── config.py         # Configuration loading/validation
│   ├── ingest.py         # Ingestion pipeline
│   ├── build.py          # Site builder
│   ├── graph.py          # Knowledge graph construction
│   ├── crossref.py       # Cross-reference extraction
│   ├── importance.py     # PageRank scoring
│   ├── clusters.py       # Connected component detection
│   ├── search.py         # SQLite FTS5 search
│   ├── serve.py          # Local HTTP server
│   ├── exporters.py      # AI export generators
│   ├── lint.py           # Quality checks
│   ├── state.py          # Build state management
│   ├── adapters/         # Ingestion adapters
│   │   ├── __init__.py   # Registry and auto-detection
│   │   ├── base.py       # BaseAdapter + WikiPage
│   │   ├── source_code.py
│   │   ├── xml_adapter.py
│   │   ├── pdf_adapter.py
│   │   ├── markdown_adapter.py
│   │   ├── config_adapter.py
│   │   └── generic_adapter.py
│   └── render/           # HTML/CSS/JS generation
│       ├── html.py
│       ├── css.py
│       └── js.py
├── tests/                # Test suite
├── docs/                 # Documentation
├── pyproject.toml        # Package configuration
└── LICENSE               # MIT License
```

---

## Code Style

LLMWiki does **not** enforce linting via CI. We ask contributors to follow these conventions:

- **Type hints**: use `from __future__ import annotations` and annotate function signatures
- **Docstrings**: module-level docstring for every `.py` file, function/class docstrings for public APIs
- **Imports**: stdlib → third-party → local, separated by blank lines
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for module constants
- **Line length**: aim for ~100 characters, not rigidly enforced
- **Dependencies**: avoid adding new pip dependencies — the 2-dependency constraint is a feature

---

## Testing

### Run the Full Suite

```bash
pytest tests/
```

### Run a Specific Test File

```bash
pytest tests/test_config.py
pytest tests/test_graph.py -v
```

### Run a Specific Test

```bash
pytest tests/test_crossref.py::test_extract_refs_from_body -v
```

### Test Coverage

The test suite covers:

| Module | Test File |
|--------|-----------|
| Adapters (all 6) | `test_source_code_adapter.py`, `test_xml_adapter.py`, `test_pdf_adapter.py`, `test_markdown_adapter.py`, `test_config_adapter.py`, `test_generic_adapter.py` |
| Base adapter | `test_base_adapter.py` |
| Build | `test_build.py` |
| CLI | `test_cli.py` |
| Clusters | `test_clusters.py` |
| Config | `test_config.py` |
| Cross-references | `test_crossref.py` |
| Exporters | `test_exporters.py` |
| Graph | `test_graph.py` |
| Importance | `test_importance.py` |
| Ingest | `test_ingest.py` |
| Lint | `test_lint.py` |
| Search | `test_search.py` |
| Serve | `test_serve.py` |
| State | `test_state.py` |
| End-to-end | `test_e2e.py` |

### Writing Tests

- Use `pytest` fixtures and `tmp_path` for temporary directories
- Test files go in `tests/` with the `test_` prefix
- Test functions use `test_` prefix
- Use `conftest.py` for shared fixtures

---

## Making Changes

### Adding a New Adapter

1. Create `llmwiki/adapters/my_adapter.py`
2. Subclass `BaseAdapter` and use the `@register` decorator
3. Add the module name to `_names` in `llmwiki/adapters/__init__.py`
4. Add tests in `tests/test_my_adapter.py`
5. Document in `docs/adapters.md`

### Adding a New CLI Command

1. Add the subparser in `llmwiki/cli.py` under the `sub.add_subparsers` section
2. Create the handler function `_cmd_name(args) -> int`
3. Add it to the `dispatch` dictionary
4. Add tests in `tests/test_cli.py`
5. Document in `docs/cli-reference.md`

### Modifying the Build Pipeline

1. The build flow is in `llmwiki/build.py` (`build_site()`)
2. Graph construction is in `llmwiki/graph.py`
3. HTML rendering is in `llmwiki/render/html.py`
4. Run `pytest tests/test_build.py tests/test_graph.py` after changes

---

## Pull Request Guidelines

1. **Branch from `main`**: create a feature branch (`git checkout -b feature/my-change`)
2. **Keep PRs focused**: one feature or fix per PR
3. **Include tests**: add or update tests for any behavioral changes
4. **Run the test suite**: `pytest tests/` must pass
5. **Update docs**: if your change affects user-facing behavior, update the relevant docs
6. **Write clear commit messages**: use conventional commits when possible
   - `feat: add YAML adapter`
   - `fix: handle empty frontmatter in markdown adapter`
   - `docs: update CLI reference with new flags`

### PR Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] No new pip dependencies unless absolutely necessary
- [ ] Documentation updated if applicable
- [ ] Code follows project conventions (type hints, docstrings)

---

## Reporting Issues

File issues on GitHub with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and OS
- Sample input (if applicable)

---

## License

By contributing to LLMWiki, you agree that your contributions will be licensed under the MIT License.
