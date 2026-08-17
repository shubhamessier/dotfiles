# RULE — AGENT GRAPHS (DIAMOND PATTERN)

Operational checklist for §1.5 of the system directive. This file is the "how"; §1.5 is the "law". When any task splits into independent pieces, this is the procedure. It does not override §1 (questioning), §2 (docs-first), §3 (code standards), §4 (stage gate), §5–§8 (API trust / security / risk), or §9 (testing) — every graph node stays fully inside those.

## 1. Decide: graph or single agent (the stop rule)

Answer one question before launching anything:

> Can I state each worker's job, input, and output so that no worker needs another worker's result to start?

- **Yes** -> the work splits. Build a graph.
- **No** -> it is a sequential chain. Keep it in one agent. Optionally split off only the independent sub-part and keep the dependent chain serial.

Fanning out over dependent work is a defect (races, duplicated effort, unmergeable conflicts). Do not do it for the appearance of speed.

## 2. Lead: write the graph down first

The lead agent plans; it does not do the work. Before any worker launches, write:

- **Nodes** — one job each, with: purpose, input, output contract (the exact shape the merge step will consume), owner (one agent), and the directive sections it must obey (e.g. §6 for Solana, §9 for tests).
- **Edges** — only real dependency arrows. `A -> B` means B cannot start until A's output exists. No "feels related" edges.
- **Skeptic assignments** — which skeptic attacks which finding, and from which lens (correctness / security / reproduce).
- **Merge criteria** — how conflicts between surviving findings are resolved. Deterministic, not "last writer wins".
- **Human-gate point** — where the graph halts for approval (§4 below).

Routing is fixed at this point. Agents fill jobs; they do not add edges mid-run. An agent that finds the graph is wrong stops and reports.

## 3. The diamond

```
            +-- worker 1 --+   +-- skeptic 1 --+
lead (plan) +-- worker 2 --+---+ skeptic 2     +-- merge -- HUMAN GATE -- act
            +-- worker 3 --+   +-- skeptic 3 --+
```

1. **Lead** plans (section 2).
2. **Workers** run the independent jobs in parallel. One job, one output, per worker.
3. **Skeptics** — separate agents, never the authoring worker — try to REFUTE each finding. Prompt them to kill it and to default to "refuted" under uncertainty. Perspective-diverse skeptics for financial / security / on-chain findings; require a majority to confirm.
4. **Merge** the survivors by the written criteria.
5. **Human gate** before anything irreversible.

Prefer `pipeline()` in the Workflow tool so each worker's finding hits its skeptic the moment it is ready. Use a barrier (`parallel()` between stages) only when the merge genuinely needs all worker outputs at once — dedup across the full set, or a zero-count early exit.

## 4. Human gate — halt before irreversible actions

Halt and request explicit human approval before any agent:

- spends money or submits anything that spends money (orders, fees, tips, gas);
- publishes, sends, or transmits to any external service or person;
- deploys or changes production / mainnet state;
- deletes or overwrites data not created in this task;
- rotates, writes, or transmits any secret or key.

At the gate present: what will happen, what is irreversible, the merged evidence, and the exact approval requested. Restart never silently re-enables a gated action. This mirrors §8 kill-switch discipline.

## 5. Hard limits (non-negotiable)

- **Bounded loops.** Skeptic/retry loops cap at 2 rounds by default. At the cap: drop the finding or escalate to the human. Never loop forever (§3.4).
- **One writer per file.** Never two agents writing the same file in parallel. Sequential, or isolated worktrees reconciled by one merge step.
- **Skeptic over self-review.** Always a separate agent. Self-review misses the author's blind spots.
- **No silent caps.** State any bounded coverage (top-N, sampling, capped rounds) explicitly. Silent truncation reads as full coverage.
- **Directive applies to every node.** Code obeys §3; Solana §6; Hyperliquid §7; funds/risk §8; all code carries §9 tests under the §9.0 build-test-build cadence.

## 6. Delivery declaration

When a task ran as a graph, the delivery states:

- graph shape (nodes and real edges);
- which jobs ran in parallel and why they were independent;
- what each skeptic tried to kill and what survived;
- how conflicts were merged;
- the exact human-gate approval requested before any irreversible step.

If the routing cannot be reconstructed from the delivery, the graph was not written down properly — fix that before delivering.

## 7. Worker prompt skeleton

```
You own ONE job in a graph. Do only this job.
INPUT: <exact input>
OUTPUT CONTRACT: <a SCHEMA, not prose — JSON Schema / serde struct the merge step deserializes>
EFFORT BUDGET: <tool-call ceiling; effort scaling 1 agent / 3-10 calls simple, 10+ complex>
CONSTRAINTS: obey CLAUDE.md §3 (code standards); load the relevant domain skill
  (solana-security / hyperliquid-security / hft-risk-kill-switch) as applies; §9 tests.
DO NOT: touch files outside <scope>; take any irreversible action; review your own output.
Return only the output contract, as a schema-valid object. Return a 1-2k-token condensed
result, not raw exploration logs. Your text IS the return value, not a message to a human.
```

Route mechanical worker jobs (grep, extraction, data-gathering) to a cheaper model (Haiku)
and reserve the strongest model for design, security, and merge nodes. See the
`structured-contracts` skill for making the OUTPUT CONTRACT a real validated schema.

## 8. Skeptic prompt skeleton

Prefer the pre-built read-only skeptic subagents (they cannot Edit/Write/Bash, so
"skeptic never writes" is structural): `skeptic-correctness`, `skeptic-security`,
`skeptic-reproduce` in `~/.claude/agents/`. For financial / security / on-chain findings
use perspective-diverse skeptics (all three lenses) and require a majority to confirm.

```
You are a SKEPTIC. Your job is to REFUTE the finding below, not to agree with it.
FINDING: <finding>
LENS: <correctness | security | reproduce>
Try to break it: construct the input/state where it is wrong, incomplete, or unsafe.
Default to refuted=true if you are uncertain. Only pass what genuinely survives.
Return (schema-valid): { refuted: bool, reason: string, failure_case: string }
```

## 9. Contracts, loop-detection, and trace (sharpened rules)

- **Contracts are schemas.** Validate each worker/skeptic output against its schema at the
  merge step before consuming it. On schema-invalid output, re-prompt that one node once
  with the exact validation error (not a blind re-ask), within the 2-round cap, then drop
  or escalate. Never merge a best-effort parse. (See `structured-contracts` skill.)
- **Loop-detection beats a blunt counter.** If a node emits the same tool call with the same
  args twice, or produces no state change across a step, treat it as stuck: abort that node
  and escalate to the human with the trajectory, rather than burning the 2-round budget.
- **Every run is traced.** The `trace_span.py` hook records one span per tool call and
  subagent stop to `~/.claude/traces/<session>.jsonl`. Reconstruct the graph's routing for
  the section-6 delivery declaration from the trace (see `observability-trace` skill) instead
  of narrating it from memory.
