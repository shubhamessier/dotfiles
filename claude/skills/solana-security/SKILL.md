---
name: solana-security
description: Solana on-chain security gauntlet - applied to every Solana program, whether user-submitted or self-written. Use when writing, reviewing, or auditing Solana/Anchor/SPL programs, CPIs, PDAs, account validation, on-chain arithmetic, account lifecycle, compute budgets, or MEV surface. Auto-load for any Solana on-chain task.
---

# Solana Security Gauntlet

Applied to every Solana program — user-submitted or self-written.

**Ownership & Authority.** Every `AccountInfo` has `.owner` validated. Every state change verifies signer. PDAs re-derived from canonical seeds on every access. Discriminators (8-byte minimum) checked on every deserialization.

**Arithmetic.** `checked_*` or `saturating_*` everywhere. Rounding direction intentional: against user for fees, favor protocol for collateral. Token decimal scaling explicit, never mixed between mints.

**State Lifecycle.** Account close: drain lamports, zero data, reassign to system program. All three or resurrection is possible. Re-entrancy guard on every CPI modifying shared state. `remaining_accounts` validated exhaustively.

**Compute.** No `find_program_address` on-chain in production. Pre-compute bumps off-chain. Minimize CPI depth (~25K CU overhead per CPI). Pre-allocate account size at init.

**MEV.** Every swap assessed for sandwich surface. Priority fees dynamic, not static. Oracle staleness window identified as MEV extraction surface.

## Context to establish before writing (Solana)

- Solana SDK version (1.18.x / 2.x Agave) and runtime target (BPF / SBF)
- Framework and exact version (Anchor 0.30.x / raw solana-program)
- Environment: Devnet / Testnet / Mainnet-Beta
- RPC endpoint class: public / private / dedicated validator (latency profile changes everything)
- Compute unit budget: default 200K or custom allocation per instruction
- Account data strategy: Borsh / zero-copy / custom layout with max account size
- Priority fee strategy: static / dynamic / Jito bundles with tip range
- MEV protection posture: Jito tips / private mempool / none
- Program upgrade authority: multisig / single key / immutable
- Existing codebase: greenfield or integrating? If existing, read the relevant modules first.
