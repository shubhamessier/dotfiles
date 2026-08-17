---
name: structured-contracts
description: How to make agent/tool/graph outputs typed and schema-validated instead of free text. Use when defining a diamond-graph worker/skeptic output contract, building a tool or MCP server, parsing model output as data, forcing JSON output, or designing a classification/verdict/extraction result. Prevents malformed-output bugs at every hand-off.
---

# Structured Contracts

Any output another step consumes as data must be a validated schema, not prose the next step re-parses. This closes a whole class of malformed-hand-off bugs.

## Rules

1. **Every contract is a schema.** A diamond-graph worker/skeptic OUTPUT CONTRACT, a tool result, an extraction, a classification — declare it as a JSON Schema (research/JS) or a serde+schemars struct (Rust). The consumer deserializes into the type; it never scrapes free text.

2. **Force it, don't ask for it.** Get JSON by giving the model a single tool whose `input_schema` IS the desired shape and setting `tool_choice` to that tool (with `strict: true` on the API where available). Do not ask for JSON in prose and regex-parse the reply. Note: prefilled-assistant-message JSON is rejected (HTTP 400) on current models — use the tool/structured-output path instead.

3. **Validate at the boundary, retry on the error.** The merge/consumer step validates the returned object against the schema before using it. On failure, re-prompt that one producer once, feeding back the exact validation error (missing field, wrong type, out-of-range) — not a blind re-ask. Cap retries (2 rounds), then drop or escalate.

4. **Closed enums for decisions.** Any decision field (verdict, severity, side, risk outcome) is a closed enum, never free text. In Rust use fieldless enums so a non-exhaustive match fails to compile; in JSON Schema use `enum`. No catch-all `_ =>` handler.

5. **Every schema has a non-answer branch.** Extraction/analysis schemas include an explicit `Uncertain` / `InsufficientEvidence` variant (or an `Option`). A schema with no non-answer branch coerces the model to fabricate a well-typed lie — especially when reading untrusted data.

6. **Push sanity bounds into the type.** Encode range checks as schema constraints (`minimum`/`maximum`) or Rust newtypes that reject out-of-range on construction (e.g. a price type that refuses negatives). Out-of-range then fails structurally and triggers the retry.

7. **Field descriptions carry units and bounds.** Every schema field states its unit, scale, and bound in its description ("unix-ms timestamp, within 5s of now"), and that wording matches the corresponding code type's doc so the model's contract and the code's contract cannot drift.

## Tool boundary

Model-facing tools (custom tools, MCP servers) validate their input against a schema at the boundary and, on failure, return a structured, observable error block (`{error: {code, detail, offending_value}}`) the model can read and self-correct from — never a bare throw, an opaque string, or a fake success. Give financial/read tools an output schema and return the typed object; encode money as decimal strings or scaled integers with unit-tagged field names, never a float.

## In the diamond-graph

The worker and skeptic prompt skeletons declare their OUTPUT CONTRACT as an explicit schema. The skeptic verdict is `{refuted: bool, reason: string, failure_case: string}` (or the `CONFIRMED|REFUTED|UNCERTAIN` enum) validated at merge. A schema-invalid producer output is rejected and retried within the loop cap, never merged as a best-effort guess.
