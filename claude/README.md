# claude

My global Claude Code config (`~/.claude`), minus machine-local state
(sessions, credentials, caches, history, traces).

- `CLAUDE.md` — engineering directive: questioning doctrine, code standards,
  stage gate, agent-graph orchestration.
- `rules/agent-graphs.md` — diamond-pattern operational checklist.
- `agents/` — read-only skeptic subagents (correctness/security/reproduce)
  used to adversarially check findings.
- `skills/` — on-demand skills referenced from CLAUDE.md (diamond-graph,
  eval-harness, structured-contracts, observability-trace, long-run-context,
  engineering-doctrine, domain skills for Solana/Hyperliquid/HFT risk).
- `hooks/` — `code_standards.py` (post-edit lint against CLAUDE.md §3),
  `trace_span.py` / `trace_view.py` (run tracing).
- `settings.json` — hook wiring, statusline, model/effort defaults.
- `statusline.sh` — status line showing cost, context %, quota, model.
- `mcp.json` — global (user-scope) MCP server definitions. The `mcpServers`
  block lives in `~/.claude.json` on the machine (not `settings.json`), and
  that file also holds machine-local session state, so only the server
  definitions are tracked here, merge them into `~/.claude.json`'s
  `mcpServers` key rather than copying the whole file. Each stdio server
  points at a global install (`npm install -g` / `uv tool install`), not
  `npx`/`uvx`, so tool startup doesn't refetch on every launch:
  - `chrome-devtools` — `npm install -g chrome-devtools-mcp`
  - `filesystem` — `npm install -g @modelcontextprotocol/server-filesystem`
  - `sequential-thinking` — `npm install -g @modelcontextprotocol/server-sequential-thinking`

To use: symlink or copy into `~/.claude/`.
