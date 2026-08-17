---
name: observability-trace
description: Read, view, and reason about agent/graph run traces emitted by the trace hook. Use to inspect what an agent or diamond-graph run actually did, debug a failed run node-by-node, reconstruct a graph's routing for a delivery declaration, or audit tool activity. Traces live at ~/.claude/traces/<session>.jsonl.
allowed-tools: Read, Bash(python3 $HOME/.claude/hooks/trace_view.py *), Bash(ls ~/.claude/traces*), Bash(cat ~/.claude/traces/*)
---

# Observability / Trace Viewer

The `trace_span.py` hook (wired in `settings.json` on `PostToolUse`, `SubagentStop`, `SessionStart`, `Stop`) appends one JSON span per lifecycle event to `~/.claude/traces/<session_id>.jsonl`. This is the run record — instrument before you optimize.

## View a run

```
python3 ~/.claude/hooks/trace_view.py latest        # most recent session
python3 ~/.claude/hooks/trace_view.py <session_id>  # a specific session
```

The viewer prints: span count and wall time, event/tool counts, which subagents finished, errors (tool calls that returned an error), and a compact timeline.

## Span schema

Each line: `ts` (epoch), `event`, `session_id`, `cwd`, and for tool events `tool_name`, `target` (short human string — file path / command head), `input_sha` (sha256 of tool input; raw args and secrets are never stored), and on `PostToolUse` a `status` of `ok`/`error`. Subagent events carry `agent_id` and `agent_type`.

## Uses

- **Debug a failed run**: open the trace, walk the timeline to the error span, see the exact tool and target that broke — instead of guessing from scrollback.
- **Reconstruct a diamond-graph run**: the `SubagentStop` spans plus the tool timeline show which workers/skeptics ran and where a chain broke — the raw material for the graph delivery declaration.
- **Audit tool activity**: what an unattended or long run actually did, in order.

## Limits

- Hooks are not given token/cost usage today, so per-node token accounting is best-effort (recorded only if a future payload carries it). For cost, cross-reference the model's own usage output.
- The `PostToolUse *` matcher traces every tool call; narrow the matcher in `settings.json` if the volume is noisy.
- To promote a known-good run into a regression fixture, snapshot its inputs and expected output into an `eval-harness` case.
