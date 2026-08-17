---
name: diamond-graph
description: Run multi-step, research-heavy, audit, migration, or review work as an agent graph using the diamond pattern — one lead plans, independent workers run in parallel, separate skeptics try to kill weak findings, survivors merge, and the human is the final gate before any irreversible action. Invoke whenever a task splits into independent pieces (multi-file/multi-source/multi-approach). Implements §1.5 of CLAUDE.md.
---

# Diamond Graph

Structure the work as a diamond agent graph per CLAUDE.md §1.5 and `.claude/rules/agent-graphs.md`. Do not lower any directive standard inside any node.

## Step 1 — Apply the stop rule

Ask: can each worker's job, input, and output be stated so no worker needs another worker's result to start?

- **No** -> this is sequential work. Do NOT build a graph. Say "single-agent — sequential work" and proceed serially. Stop here.
- **Yes** -> continue.

## Step 2 — Lead writes the graph (before launching anything)

Produce the written plan and show it in the GRAPH PLAN line of the response:

- **Nodes**: one job each — purpose, input, output contract, single owner, directive sections it must obey (§3 always; §6/§7/§8/§9 as applies).
- **Edges**: real dependency arrows only. `A -> B` means B cannot start until A's output exists.
- **Skeptic assignments**: which skeptic attacks which finding, from which lens (correctness / security / reproduce).
- **Merge criteria**: deterministic conflict resolution.
- **Human-gate point**: where the graph halts for approval.

Routing is fixed here. Agents fill jobs; they never add edges mid-run.

## Step 3 — Launch the diamond

Prefer the Workflow tool. Skeleton (pipeline so each finding is checked as soon as it is ready):

```
lead plans -> parallel workers -> per-finding skeptic(s) -> merge survivors -> HUMAN GATE
```

- Workers: independent, one job / one output each. Never two writers to one file. Each worker's OUTPUT CONTRACT is a schema (see `structured-contracts`), validated at merge; route mechanical jobs to a cheaper model and give each a tool-call/effort budget.
- Skeptics: use the pre-built read-only agents `skeptic-correctness`, `skeptic-security`, `skeptic-reproduce` (they cannot Edit/Write/Bash, so "skeptic never writes" is structural). Prompted to REFUTE and default to "refuted" under uncertainty. Perspective-diverse + majority-to-confirm for financial/security/on-chain findings. Never the worker that produced the finding.
- Use a barrier only when the merge needs all worker outputs at once (dedup, zero-count early exit).
- Large fleets are opt-in: propose the orchestration and let the human authorize the spend.
- The run is traced automatically (`trace_span.py` hook -> `~/.claude/traces/<session>.jsonl`); reconstruct the routing for the Step 6 delivery declaration from the trace via the `observability-trace` skill, and detect stuck nodes (same call twice / no state change) to abort rather than burn the retry budget.

Worker and skeptic prompt skeletons are in `.claude/rules/agent-graphs.md` sections 7–9.

## Step 4 — Bounded loops

Skeptic/retry loops cap at 2 rounds. At the cap: drop the finding or escalate to the human. Never loop forever (§3.4).

## Step 5 — Human gate (mandatory)

Halt and request explicit human approval before anything that spends money, publishes, sends, deploys, changes production state, deletes/overwrites pre-existing data, or touches a secret/key. Present: what will happen, what is irreversible, the merged evidence, the exact approval requested. Restart never re-enables a gated action.

## Step 6 — Delivery declaration

State the graph shape (nodes + real edges), which jobs ran in parallel and why they were independent, what each skeptic tried to kill and what survived, how conflicts merged, and the exact human-gate approval requested. If the routing can't be reconstructed from the delivery, the graph wasn't written down properly.
