---
name: long-run-context
description: Discipline for long, multi-step, multi-window build/migration/audit runs so context exhaustion and compaction do not lose state or drift the agent off its constraints. Use for any task expected to span many tool calls or a context compaction - large feature builds, migrations, sweeps, long agent loops.
---

# Long-Run Context Discipline

Context is finite and recall degrades as it fills ("context rot"); compaction drops detail. On long runs, persist state to files, load context just-in-time, and re-anchor constraints so the agent does not forget its guardrails or stop early.

## Persist state in files, not context

- **Feature/test ledger** `NOTES.md` or `.claude/progress/<project>.json`: one entry per feature `{name, success_criterion, status: pending|green|red, test_command, last_run}`. The build loop reads it on start and resumes at the first non-green feature; a green feature is never rebuilt. This makes "no feature built on an untested feature" checkable, not aspirational.
- **Progress log**: `done / next / open-bugs / decisions`. Update it as you go, not at the end.
- **Checkpoints**: commit to git at each green feature so a crash or context reset resumes from the last good state.
- Treat editing or removing a test in the ledger as forbidden — tests only get added or turned green.

## Load context just-in-time

- Pass file paths and queries into sub-tasks; let them Read on demand. Do not paste whole modules into a prompt.
- Prefer lightweight identifiers over pre-loading corpora.
- Use `/clear` between unrelated tasks rather than accreting one giant session.

## Survive compaction

- When compacting, always preserve: the list of modified files, the current failing test, all ADR/changelog decisions, and any pending risk/safety items.
- Include an explicit instruction on long autonomous runs: "your context may be compacted; save state to the ledger before continuing and do not stop early on token-budget grounds."

## Re-anchor constraints (fight instruction drift)

- Maintain an explicit objective/TODO line and restate it as you complete steps, rather than assuming the top-of-context instructions still hold.
- After a significant tool result, re-emit a compact status block: current sub-goal, the specific standing constraints for this work (e.g. the banned-behavior rules, any human-gate-before-irreversible-action rule), and what changed in the environment.
- Keep the stable instruction prefix (CLAUDE.md, skills, tool defs) positionally stable across turns so it stays cached; a falling cache-hit rate is an early signal that the constraint prefix moved — investigate before trusting output.

## Ground answers in current state

For any question about live external state (chain, exchange, filesystem, API), use tools to verify before answering; do not answer from memory. State-dependent answers from memory are the common silent-failure mode on long runs.
