---
name: hft-risk-kill-switch
description: Risk framework, pre-trade risk gate, kill switch, and post-trade reconciliation for any system that places orders or manages capital. Use when building or reviewing trading execution, order submission, position/exposure management, or any code that can move funds. Auto-load for any capital-moving task.
---

# Risk Framework & Kill Switch

For any system that can place orders or move funds. This is the operational backbone; a capital-moving system without it does not ship.

## Pre-Trade Risk Gate

Every check runs even if an earlier check fails. A full violation report is logged.

Required checks: position size cap, gross exposure cap, single-order fat-finger limit, drawdown threshold, orders-per-second limit, open order limit, asset whitelist, global kill switch flag, margin sufficiency (queried, not assumed), slippage guard.

## Kill Switch

Present in every trading system. Tested on every deployment.

Execution sequence:
1. Set `trading_enabled` to false (atomic). No new orders from this instant.
2. Cancel all open orders across all venues. Wait for confirmation.
3. Flatten all positions with market orders. Accept and log slippage.
4. Alert to external channel.
5. Persist kill state to disk. Restart does not re-enable. Manual intervention required.

Triggers: max drawdown, position desync, WS disconnect >60s, abnormal slippage (>10x expected), auth failure, unrecognized error code from exchange, manual (SIGUSR1 / CLI).

## Post-Trade Reconciliation

After every fill: update local state from fill event, reconcile against exchange within 500ms, halt on any desync, log full trade details (timestamp, IDs, prices, slippage, fees, position, margin, liquidation price).

## Relationship to the human gate

The kill switch and the agent-graph human gate (see `.claude/rules/agent-graphs.md`) are the same posture: no irreversible action — order, tip, transfer, deploy, key write — proceeds without an explicit, hard, out-of-model control, and a restart never silently re-enables a gated action. Prefer enforcing these as deterministic hooks/permissions over prose the model is trusted to honor.
