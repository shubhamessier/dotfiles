---
name: eval-harness
description: Regression eval harness for Claude Code prompts, agents, and generated code. Use when asked to run evals, add an eval case, check for prompt/model regressions, before changing CLAUDE.md or a skill, or before shipping a prompt/agent to production. Grades deterministically (build/lint/regex/JSON-schema) first, LLM-judge only for subjective properties.
allowed-tools: Read, Write, Edit, Bash(python3 ${CLAUDE_SKILL_DIR}/*), Bash(git *)
---

# Eval Harness

Zero-dependency regression harness. Replays frozen task cases through `claude -p --output-format json`, grades each with `assertions.py`, writes a versioned result, and diffs against a baseline. Turns "the output feels fine" into a number that gates change.

Files (all under `${CLAUDE_SKILL_DIR}`):
- `runner.py` — replay + grade + baseline diff. `python3 runner.py [--cases f] [--model m] [--dry] [--self-test] [--update-baseline]`
- `assertions.py` — deterministic assertion library + JSON-schema validator + `llm_judge`.
- `cases/*.jsonl` — one case per line. `starter.jsonl` ships as examples; replace with your real tasks.
- `results/` — `run-<epoch>.json` per run, `baseline.json` is the reference.

## When to run it

- Before and after any edit to `CLAUDE.md`, a skill, an agent, or a worker prompt — diff the pass rate.
- On any model-id change (you are pinned to a specific model; a bump can silently degrade adherence).
- As the final gate before a prompt/agent ships to production (the testing gate in CLAUDE.md).
- Wire `python3 runner.py` into a git pre-push hook or CI. Non-zero exit = a case failed or regressed.

## Grade cheapest-first

Layer assertions so cheap deterministic checks dominate and the model-graded ones are last resort:
1. `shell` running the real toolchain on generated code (`cargo build`, `cargo clippy -- -D warnings`, `tsc --noEmit`, `pytest`) via the `extract` step.
2. `regex`/`not_regex`/`contains*` for banned-token and required-shape checks.
3. `json_valid` + `json_schema` for any structured output.
4. `llm_judge` only for genuinely subjective properties (prose quality, faithfulness).

Assertion types: `regex`, `not_regex`, `contains`, `not_contains`, `contains_any`, `contains_all`, `json_valid`, `json_schema` (`schema` inline or `schema_file`), `shell` (`cmd`, `cwd`, `expect_exit`, `timeout`), `max_tokens`, `max_cost_usd`, `max_tool_calls`, `llm_judge` (`rubric`, `threshold`, `judge_model`). Each supports `desc`, `weight`, and `critical` (default true — a failing critical assert fails the case).

## Case format

```json
{"id": "no-unwrap-in-generated-rust",
 "prompt": "Write a Rust function ... using checked arithmetic. No unwrap.",
 "extract": {"lang": "rust", "to": "gen.rs"},
 "asserts": [
   {"type": "not_regex", "pattern": "\\.unwrap\\(\\)", "desc": "no unwrap"},
   {"type": "contains_any", "values": ["checked_", "saturating_"]},
   {"type": "shell", "cmd": "rustc --edition 2021 --crate-type lib $CODE_FILE -o /dev/null", "desc": "compiles"}
 ],
 "mock": "canned output used only by --dry"}
```

`extract` pulls the first fenced code block into a temp file; `shell` asserts then run in that temp dir with `$CODE_FILE` set — this is how you actually compile/lint generated code rather than trusting a judge.

## The regression flywheel

Every defect you catch in Claude's output — bad code, a hallucinated API, a missed check — becomes a new case here before you move on. Append `{prompt, failure_mode, assert}` that reproduces it. Re-run the full suite on any model or directive change. This is the failing-test-first discipline lifted to the prompt/agent level.

## LLM judge discipline

Before trusting any `llm_judge`: align it against your own labels on ~25-30 examples, tune the rubric until judge/human precision and recall on the "bad" class are both high, then freeze the rubric. Grade with a different model than the one under test. Re-align on any rubric or judge-model change.

## Verify offline

`python3 runner.py --self-test` runs the assertion unit tests (no model calls). `python3 runner.py --dry` grades each case's `mock` field (no model calls) — use both to validate the harness itself before a live run.
