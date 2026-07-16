# Token Efficiency

## Why Token Efficiency Matters

AI agents like Copilot, Claude, and Cursor consume tokens when reading source files to answer questions. A typical codebase query might require reading 10-20 files (50,000-200,000 tokens), but the answer often comes from just a few key sections.

LLMWiki pre-processes your codebase into focused summaries, cross-references, and searchable indexes. When agents query the wiki instead of reading raw files, they get the same information with 90-98% fewer tokens.

**Impact:**
- **Cost**: At $5/million tokens (GPT-4), a team making 100 queries/day saves ~$15-50/day
- **Speed**: Smaller context = faster responses
- **Accuracy**: Focused summaries reduce noise and hallucination risk
- **Context window**: Fits within smaller context windows (important for local models)

## How It Works

1. `llmwiki ingest` extracts structure from source files (classes, methods, imports, docs)
2. `llmwiki build` generates searchable summaries with cross-references
3. Agents query the wiki via MCP tools, CLI, or search index
4. Only raw files are read when the wiki doesn't have the answer

## Measuring Token Savings

### Benchmark Command

```bash
llmwiki benchmark "how does authentication work"
```

This compares:
- **Without wiki**: Tokens in all source files matching the query keywords
- **With wiki**: Tokens in wiki search results for the same query

### Before/After Demo

1. Disable wiki-first mode:
   ```bash
   llmwiki agent --disable
   ```
2. Ask your AI agent a question — note the token usage
3. Enable wiki-first mode:
   ```bash
   llmwiki agent --enable
   llmwiki build  # regenerate agent instructions
   ```
4. Ask the same question — note the reduced token usage
5. The difference is your real savings

### Dashboard Stats

The wiki dashboard shows live token efficiency numbers:
- **Raw tokens**: Total tokens in your source files
- **Wiki tokens**: Total tokens in wiki summaries
- **Compression**: Percentage reduction

## Setting Up Agent Integration

```bash
# Install MCP configs for your IDE
llmwiki setup-agent --all

# Or choose specific IDEs
llmwiki setup-agent --vscode
llmwiki setup-agent --cursor
llmwiki setup-agent --jetbrains

# Enable wiki-first mode
llmwiki agent --enable
```

See [AI Integration](ai-integration.md) for full details on generated files and formats.

## ROI Calculator

| Metric | Without Wiki | With Wiki |
|--------|-------------|-----------|
| Tokens per query | ~80,000 | ~2,000 |
| Cost per query (GPT-4) | ~$0.40 | ~$0.01 |
| Queries per day (team) | 100 | 100 |
| Daily cost | ~$40 | ~$1 |
| Monthly savings | | ~$1,170 |
