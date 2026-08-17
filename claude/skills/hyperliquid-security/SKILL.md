---
name: hyperliquid-security
description: Hyperliquid L1 security gauntlet - EIP-712 signing, order lifecycle, connection resilience, and risk awareness. Use when writing, reviewing, or auditing any Hyperliquid integration - signing, order placement/modify/cancel, websocket feeds, margin/funding/liquidation logic. Auto-load for any Hyperliquid task.
---

# Hyperliquid Security Gauntlet

**Signing.** EIP-712 domain chain ID matches target environment. Wrong chain ID = silent rejection (HTTP 200 with error body). Signature locally verified before transmission. Nonce strictly monotonically increasing with collision avoidance under high throughput.

**Order Lifecycle.** Margin queried and validated before submission. Response parsed for application-level status, not just HTTP code. Fill confirmation via WebSocket user-events, not polling. Local state reconciled against `/info` within 500ms of fill. Modify (cancel-replace) is atomic — never separate cancel + place.

**Connections.** WS isolated by feed type. Reconnect with backoff, sequence gap detection, snapshot re-request, heartbeat timeout.

**Risk Awareness.** Funding rate annualized before every position open. Liquidation price computed locally and surfaced. Mark-to-market via real-time WS feed.

## Context to establish before writing (Hyperliquid)

- SDK: `hyperliquid-python-sdk` version / raw REST+WS in Rust / TypeScript
- API target: mainnet (`https://api.hyperliquid.xyz`) / testnet, and the exact chain ID for EIP-712 signing
- Signing stack: ethers-rs / alloy / ethers.js / web3.py with version
- Margin mode: Isolated / Cross
- Slippage tolerance in basis points
- Nonce strategy: timestamp-ms with collision counter / custom
- WebSocket feeds: L2 book / trades / user events / candles — which ones and at what frequency
- Vault address if operating through a vault
- Current known rate limits for target endpoints (verify independently; HL has throttled below documented limits under load)
