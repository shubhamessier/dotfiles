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

To use: symlink or copy into `~/.claude/`.
