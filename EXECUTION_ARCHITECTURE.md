# SYRAX — Unified Execution Gateway Architecture & Safety Invariants

## 1. Executive Summary & Core Philosophy

In SYRAX, **execution authority is strictly separated from decision-making, natural language reasoning, and model outputs**.

Neither LLM responses, user chats, external MCP commands, REST API calls, nor autonomous background daemons are permitted to execute trades, place orders, or modify portfolio balances directly.

All trade intents from every surface MUST construct a strongly typed `ExecutionRequest` and pass it through the **`UnifiedExecutionGateway` (`agent/execution_gateway.py`)**.

```
                           ┌────────────────────────────────────────┐
                           │          INCOMING INTENTS              │
                           │  - Natural Language Chat / LLM Brain   │
                           │  - User Confirmation UI Action Card    │
                           │  - REST API (/api/subwallet/*)         │
                           │  - Model Context Protocol (MCP Tools)  │
                           │  - 24/7 Autonomous Sentinel Daemon     │
                           └──────────────────┬─────────────────────┘
                                              │
                                              ▼
                        ┌──────────────────────────────────────────┐
                        │        ExecutionRequest Object           │
                        │  (symbol, action, notional, sl, tp, id)  │
                        └──────────────────┬───────────────────────┘
                                              │
                                              ▼
          ═════════════════════════════════════════════════════════════════════
          ███████████  UNIFIED EXECUTION GATEWAY (9-STAGE PIPELINE)  ██████████
          ═════════════════════════════════════════════════════════════════════
          │ 1. Idempotency & Replay Attack Filter                             │
          │ 2. Schema & Positive Value Validation                             │
          │ 3. Environment & Live Market Data Verification                    │
          │ 4. Mandatory Stop-Loss Enforcement (Zero-tolerance naked risk)    │
          │ 5. Hard Safety Invariants (Max Leverage & Order Size Rejection)   │
          │ 6. Central RiskEngine Evaluation (VaR, Drawdown, Cash Margin)     │
          │ 7. News & Threat Radar Sentry Veto Hook (Exploit/Halt checks)     │
          │ 8. Isolated Execution Engine (Simulation vs Live Binance Sub-Acc) │
          │ 9. Cryptographic Audit Receipt Generation                         │
          ═════════════════════════════════════════════════════════════════════
                                              │
                                              ▼
                        ┌──────────────────────────────────────────┐
                        │        Standardized ExecutionReceipt     │
                        │   - status: SUCCESS / REJECTED / BLOCKED │
                        │   - environment: SIMULATED / LIVE_BINANCE│
                        │   - audit_trail: Timestamps & Checks     │
                        └──────────────────────────────────────────┘
```

---

## 2. The 9-Stage Deterministic Safety Pipeline

When `gateway.execute(request)` is called, the request progresses through nine sequential gate stages. If any stage fails, the pipeline immediately short-circuits, rejecting or blocking the order and returning an explicit failure `ExecutionReceipt`. **Safety violations are never silently clamped or modified.**

### Stage 1: Idempotency & Replay Verification
- Every request carries an `idempotency_key` (generated or derived from timestamp + payload).
- Gateway maintains an LRU execution cache. Duplicate requests return the original receipt immediately, preventing double fills during network retries.

### Stage 2: Strict Request Validation
- Verifies required fields: symbol, quantity/notional > 0, price > 0.
- Rejects malformed requests before touching market data or risk subsystems.

### Stage 3: Environment & Market Data Verification
- Validates environment (`SIMULATED`, `BINANCE_TESTNET`, `BINANCE_AGENTIC_SUB_ACCOUNT`, `LIVE_BINANCE`).
- Queries live Binance market ticker. If ticker price is non-positive or unavailable, the trade is rejected (Fail-Closed).

### Stage 4: Mandatory Stop-Loss Gating
- Open position actions (`OPEN_POSITION`) strictly require a positive `stop_loss`.
- If a user/caller does not supply an explicit stop loss, the gateway applies a mandate-compliant conservative stop loss (or rejects if strictly required).
- Naked risk exposure (trades without a stop loss) is mathematically impossible.

### Stage 5: Hard Safety Invariants (No Silent Clamping)
- Mandate checks:
  - `leverage <= max_leverage` (Mandate maximum: default 3x spot/perp).
  - `notional_usd <= max_order_size_usd` (Mandate maximum: default $50.00).
- **Rule**: If a request violates these limits, SYRAX **rejects** the order with an explicit explanation rather than silently clamping the leverage or quantity.

### Stage 6: Central `RiskEngine.evaluate(...)`
- Evaluates total portfolio cash reserve, single-asset concentration limits, account risk allocation (e.g. 1.0% maximum dollar risk), Value-at-Risk, and max portfolio drawdown.
- If RiskEngine decision is not `APPROVED`, execution halts immediately.

### Stage 7: Sentry Threat Radar Veto Hook
- Interrogates `NewsSentryAgent` for live high/critical security exploits, smart contract hacks, depeg events, or trading halts on the target token.
- If an active threat is identified, the gateway raises an emergency **SENTRY VETO** and blocks execution.

### Stage 8: Low-Level Isolated Adapter Execution
- Physical execution is dispatched strictly to the appropriate adapter:
  - `SIMULATED`: Dispatched to `SubWalletManager`.
  - `BINANCE_AGENTIC_SUB_ACCOUNT` / `LIVE_BINANCE`: Dispatched to `BinanceAgentOS`.
- Low-level methods (`sub_wallet.open_trade`, `binance_os.execute_order`) are never exposed directly to external callers.

### Stage 9: Standardized Execution Receipt
- Produces a unified `ExecutionReceipt` containing:
  - Order ID & Execution ID
  - Explicit execution environment (`SIMULATED` vs `LIVE_BINANCE`) — prevents simulated trades from ever being misrepresented as live exchange fills.
  - Fees, timestamps, filled price, quantity, and comprehensive multi-checkpoint audit trail.

---

## 3. Entry Point Verification & Anti-Bypass Guarantees

| Originating System | Entry Point | Integration Mechanism | Bypass Status |
| :--- | :--- | :--- | :--- |
| **Conversational AI Brain** | `agent/orchestrator.py` (`_handle_execute_trade`) | Routes via `self.gateway.execute(...)` | 🔒 Protected |
| **User Confirmation Card** | `agent/orchestrator.py` (`execute_confirmed_action`) | Routes via `self.gateway.execute(...)` | 🔒 Protected |
| **REST API (Market Order)** | `backend/main.py` (`/api/subwallet/order`) | Routes via `orchestrator.gateway.execute(...)` | 🔒 Protected |
| **REST API (Limit Order)** | `backend/main.py` (`/api/subwallet/limit-order`) | Routes via `orchestrator.gateway.execute(...)` | 🔒 Protected |
| **REST API (Close/Cancel)** | `backend/main.py` (`/api/subwallet/close`, `/cancel`) | Routes via `orchestrator.gateway.execute(...)` | 🔒 Protected |
| **MCP Tools** | `backend/mcp_server.py` (`syrax_execute_trade`, `syrax_manage_trade`) | Routes via `orchestrator.gateway.execute(...)` | 🔒 Protected |
| **24/7 Sentinel Daemon** | `backend/monitor_daemon.py` (Auto SL/TP Triggers) | Routes via `gateway.execute(...)` | 🔒 Protected |

---

## 4. Environment Transparency

SYRAX enforces total truthfulness in trade reporting:
- `SIMULATED`: Generated when running in local memory or dry-run mode. Receipts explicitly state `"environment": "SIMULATED"` and `"simulated": true`.
- `LIVE_BINANCE`: Generated only when confirmed and filled against the Binance API with real order identifiers.
- Synthetic/mock exchange IDs are never forged to look like real Binance exchange hashes.
