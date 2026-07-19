# Token Efficiency

## The honest version

Modern coding agents (Claude Code, Copilot, Cursor) do not read whole
codebases — they grep for terms and read a handful of matching files.
That baseline is already efficient for source code. Any tool claiming
"90%+ savings on every query" is comparing against a strawman.

Where LLMWiki genuinely saves tokens:

1. **Un-greppable sources.** Agents cannot grep PDFs at all, and vendor
   XML/config is noisy to search. LLMWiki turns both into FTS5-indexed
   pages — the difference between "impossible/expensive" and "one search".
2. **Navigation queries.** "Which file declares `refreshToken`?",
   "what references this class?" — `llmwiki search "method:refreshToken"`
   and the cross-reference graph answer these without opening any file.
3. **Repeated orientation.** Architecture/overview questions answered
   from page summaries instead of re-reading the same 5 files each session.

Where it does NOT save tokens: a specific code question about a file the
agent would grep straight to. The agent should read the file; the wiki's
job there is only to point at the right one. The generated agent
instructions and staleness warnings are written accordingly.

## Measuring — `llmwiki benchmark`

```bash
llmwiki benchmark "how does authentication work"
```

The benchmark compares:

- **Baseline**: a simulated grep-and-read agent — files ranked by
  distinct query-term hits, top 5 matches read in full. This mirrors how
  real agents behave; it deliberately does *not* count every
  keyword-matching file in the tree.
- **Wiki flow**: `llmwiki search --agent` output plus one
  `llmwiki get` of the top page (embedded source stripped).

The methodology is printed with every report, and the report will state
plainly when the wiki flow costs *more* tokens than reading the files —
that's a valid outcome on code-centric queries. Token counts are `len/4`
estimates, not billing math.

## Staleness: the hidden token cost

A stale index is worse than no index — an agent acting on outdated
context burns more tokens recovering than it ever saved. LLMWiki
therefore:

- records mtime/size/hash of every ingested file;
- prepends a `⚠ index is STALE` warning to every `search`/`get`/MCP
  response when the source tree has drifted, telling the agent to prefer
  raw files or re-run `llmwiki all`;
- provides `llmwiki status` (exit code 1 when stale) for hooks/CI.

After large edit sessions, re-run `llmwiki all` (incremental — only
changed files are re-processed).

## Keeping the instruction overhead small

Token-saving tooling that injects a 50-line block into every
conversation's context is self-defeating. `llmwiki setup-agent --cli`
adds a ~15-line marked section to CLAUDE.md / AGENTS.md /
copilot-instructions.md, and `llmwiki build` only refreshes sections
that already exist — it never creates or appends to your instruction
files on its own.

## Setting up agent integration

```bash
llmwiki setup-agent --cli    # compact CLI instructions (works everywhere)
llmwiki setup-agent --mcp    # MCP configs, where your IDE allows MCP
llmwiki agent --enable       # opt into wiki-first phrasing in instructions
```

See [AI Integration](ai-integration.md) for full details on generated
files and formats.
