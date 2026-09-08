# 🦅 SYRAX — Autonomous AI Trading & Portfolio Management Agent
### *Powered by Binance Agent OS, Google Gemini & Model Context Protocol (MCP)*

---

## 📌 Table of Contents
1. [Project Overview & Philosophy](#1-project-overview--philosophy)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Multi-Agent Cognitive Core](#3-multi-agent-cognitive-core)
4. [Unified Execution Gateway (8-Stage Pipeline)](#4-unified-execution-gateway-8-stage-pipeline)
5. [Cryptographic Order Ticket & Confirmation System](#5-cryptographic-order-ticket--confirmation-system)
6. [Binance Sub-Account & 5-Wallet Ecosystem](#6-binance-sub-account--5-wallet-ecosystem)
7. [Fee Transparency & Balance Deduction Engine](#7-fee-transparency--balance-deduction-engine)
8. [On-Demand AI Execution Control ("Stop Execution")](#8-on-demand-ai-execution-control-stop-execution)
9. [24/7 Security Sentry & Post-Trade Guardian](#9-247-security-sentry--post-trade-guardian)
10. [Autonomous Event-Driven Order Fill Simulator](#10-autonomous-event-driven-order-fill-simulator)
11. [Complete Frontend UI & Navigation Tour (7 Main Views)](#11-complete-frontend-ui--navigation-tour-7-main-views)
12. [Interactive Modals & Settings Control](#12-interactive-modals--settings-control)
13. [Comprehensive Backend REST & MCP API Reference](#13-comprehensive-backend-rest--mcp-api-reference)
14. [How to Run & Deploy](#14-how-to-run--deploy)
15. [Summary Checklist of Project Capabilities](#15-summary-checklist-of-project-capabilities)

---

## 1. Project Overview & Philosophy

**SYRAX** is a production-grade, autonomous and assisted AI Trading and Portfolio Management Agent built for the **Binance Agent OS Hackathon**. It combines deep reasoning capabilities (powered by Google Gemini), official exchange integrations (Binance REST, WebSocket, and Model Context Protocol), real-time safety guardrails, and deterministic mathematical risk management.

### 🛡️ Core Mandate & Non-Negotiable Invariants
1. **Strict 1.0% Maximum Dollar Loss Mandate:** No trade or portfolio action can risk more than 1.0% of user capital ($5.00 on a $500 capital base).
2. **Mandatory Stop-Loss:** Every trade must have a mathematically validated Stop Loss enforced before execution.
3. **Two-Phase Commit Order Gating:** The AI **never** executes orders autonomously without generating a cryptographically hashed, TTL-bound Order Ticket requiring explicit human confirmation.
4. **No Double Spending / Strict Capital Reservation:** Limit orders immediately reserve cash margin or token holdings.
5. **Zero Untracked Losses:** 24/7 Post-Trade Guardian continuously monitors open positions and alerts on abnormal market conditions.
6. **Exploit Defense Radar:** 24/7 Sentry scanning blocks trades on compromised tokens, smart contracts, or depegged assets.

---

## 2. High-Level Architecture

```mermaid
graph TD
    User([User / Trader]) -->|Natural Language & UI Actions| Frontend[Next.js 14 Frontend UI]
    Frontend -->|REST & WebSockets| Backend[FastAPI Backend Server :8001]
    
    subgraph Cognitive Engine [Multi-Agent Cognitive Core]
        Backend --> Orchestrator[Syrax Orchestrator]
        Orchestrator --> MarketAgent[Market Analysis Agent]
        Orchestrator --> RiskAgent[Mathematical Risk Engine]
        Orchestrator --> SentryAgent[24/7 Sentry Radar]
    end
    
    subgraph Safety & Execution Layer
        Orchestrator --> TicketRegistry[Order Ticket Registry (SHA-256 + 120s TTL)]
        TicketRegistry --> Gateway[Unified Execution Gateway (8 Stages)]
    end
    
    subgraph Binance Infrastructure
        Gateway --> SubWallet[5-Wallet Sub-Account Manager]
        Gateway --> BinanceMCP[Official Binance Agent OS MCP]
        SubWallet --> LiveBinanceAPI[Binance Spot / Futures REST & WS]
    end
    
    subgraph Continuous Protection
        Backend --> Guardian[24/7 Post-Trade Guardian]
        Backend --> Daemon[Autonomous Monitor Daemon]
    end
```

---

## 3. Multi-Agent Cognitive Core

The SYRAX backend operates as an orchestrated ensemble of specialized agents:

### A. Syrax Orchestrator (`agent/orchestrator.py`)
- **Multilingual Natural Language Processing:** Understands English, Banglish, and Bengali commands (e.g., *"5$ worth of pump kinte"*, *"Open 10x long on BTC SL 76k"*, *"amar asset ki ki ache"*).
- **12+ Distinct Intent Classifiers:**
  - `TRADE_INTENT` (Spot Buy/Sell, Futures Long/Short, Limit Orders)
  - `PORTFOLIO_QUERY` (Holdings, valuations, wallet breakdown)
  - `RISK_AUDIT` (Mandate compliance, risk exposure analysis)
  - `DISCOVERY_INTENT` (Top gainers, volume scanners, alpha gems)
  - `PROTECT_INTENT` (Emergency capital defense, de-risking)
  - `REBALANCE_INTENT` (Rebalancing portfolio to target asset ratios)
  - `CONVERT_INTENT` (Idle stablecoin consolidation)
  - `EXPLANATION_INTENT` (Technical thesis, bull/bear scenarios)
- **Conversation State Manager:** Tracks active context assets, session history, and execution context.

### B. Market Analysis Agent (`agent/market_agent.py`)
- **Multi-Timeframe Trend & Momentum:** Analyzes moving averages, RSI, and MACD indicators.
- **Orderbook Depth & Spread Inspection:** Computes live bid-ask spread in basis points (bps) and L1/L2 orderbook depth.
- **Liquidity Quality Rating:** Classifies liquidity as `HIGH`, `MEDIUM`, or `LOW`.
- **AI Score (0–100):** Weighted algorithmic score measuring setup quality.
- **Tradeability Labeling:**
  - `TRADEABLE`: Clean trend, tight spread, high liquidity.
  - `WATCH`: Developing setup, waiting for trigger.
  - `TRAP`: High slippage or manipulated volume.
  - `AVOID`: Low liquidity or high spread risk.

### C. Mathematical Risk Engine (`agent/risk_agent.py`)
- **1.0% Max Loss Enforcement:** Calculates maximum permissible loss in dollars:
  $$\text{Max Dollar Loss} = \text{Allocated Capital} \times \frac{\text{Max Risk \%}}{100} = \$500 \times 1.0\% = \$5.00$$
- **Volatility-Adjusted Position Sizing:**
  $$\text{Position Size} = \frac{\text{Max Dollar Loss}}{|\text{Entry Price} - \text{Stop Loss}|}$$
- **Risk-Reward Ratio (RRR) Gating:** Discards setups with RRR $< 1.5$.
- **Leverage Invariants:** Hard ceiling capped at 10x leverage.

### D. Sentry Exploit Radar (`agent/sentry_agent.py`)
- **24/7 Security Scanning:** Continuously parses security advisories, on-chain anomalous activity, bridge exploit reports, and smart contract vulnerability disclosures.
- **Severity Levels:** `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- **Automatic Trade Veto:** If a token has an active `CRITICAL` or `HIGH` exploit flag, order compilation is blocked immediately.

---

## 4. Unified Execution Gateway (8-Stage Pipeline)

Every single execution request in SYRAX must sequentially pass through the **8-Stage Atomic Execution Pipeline** in `agent/execution_gateway.py`:

```
[ Stage 1: Idempotency Verification ] ──▶ Checks unique UUID to prevent double execution.
[ Stage 2: Input & Schema Validation ] ──▶ Validates symbols, sides, order types.
[ Stage 3: Live Market Data Check ]   ──▶ Verifies real-time Binance bid-ask and price freshness.
[ Stage 4: Mandatory SL Enforcement ] ──▶ Rejects orders missing a valid Stop-Loss price.
[ Stage 5: Hard Invariants Gate ]     ──▶ Enforces leverage <= 10x and notional limits.
[ Stage 6: Risk Engine Dollar-Cap ]   ──▶ Enforces max dollar risk <= $5.00.
[ Stage 7: Sentry Security Radar ]    ──▶ Verifies 0 active security exploits on the asset.
[ Stage 8: Low-Level Adapter Route ]  ──▶ Routes to Binance MCP Client or Simulated Sub-Wallet.
```

If any stage fails, execution is halted, the order ticket is marked `REJECTED_BY_GATEWAY`, and a detailed audit receipt is logged.

---

## 5. Cryptographic Order Ticket & Confirmation System

To completely eliminate accidental or hallucinated AI trades, SYRAX uses a deterministic **Two-Phase Commit Gating Protocol**:

1. **Phase 1 — Ticket Compilation:**
   - The AI compiles an `OrderTicket` with exact parameters (Symbol, Side, Quantity, Notional USD, Entry, Stop Loss, Take Profit, Leverage, Est. Fee).
   - Generates a **SHA-256 Checksum** of all parameters.
   - Assigns a unique Parent Order ID (e.g., `PO-C577A5`).
   - Starts a **120-second TTL live countdown timer**.
2. **Phase 2 — Explicit User Authorization:**
   - The user authorizes the trade via the UI button or typing the exact command:  
     `CONFIRM PO-XXXXXX`
   - The Gateway verifies the cryptographic hash. If parameters were modified or the TTL expired, execution is strictly refused.
   - **Idempotency Guarantee:** If the user clicks Confirm twice, the gateway recognizes the already-executed state and returns the existing filled position details without throwing an error.

---

## 6. Binance Sub-Account & 5-Wallet Ecosystem

SYRAX provides an isolated, multi-wallet sub-account accounting engine (`backend/binance/sub_wallet.py`) reflecting real Binance wallet architecture:

### 💼 The 5 Active Binance Wallets
1. **`SPOT` (Fiat & Spot):** Main Spot trading, deposits, and token conversion account.
2. **`FUNDING` (Funding Wallet):** P2P trading, Binance Pay, crypto card, and merchant settlements.
3. **`USDT_FUTURES` (USDⓈ-M Futures):** USDT/USDC margined perpetual and delivery contracts.
4. **`COIN_FUTURES` (Coin-M Futures):** Crypto-margined perpetual contracts (BTC, ETH collateral).
5. **`CROSS_MARGIN` (Cross Margin):** Leveraged spot trading with shared collateral across pairs.

*(Note: The `EARN` wallet is intentionally excluded from active trading funds to prevent risk to locked staking assets).*

### 🔄 Multi-Wallet Features
- **Zero-Fee Internal Transfers:** Move funds between any of the 5 wallets instantly with 1-click execution.
- **Interactive Asset Drawer:** Click on any wallet card to inspect:
  - Free vs. Locked token quantities.
  - Live USD valuation based on real-time Binance prices.
  - Portfolio percentage share.
- **All Tokens Matrix:** Global asset table aggregating balances across all 5 wallets.

---

## 7. Fee Transparency & Balance Deduction Engine

Unlike simulated bots that ignore trading fees, SYRAX implements **full mathematical fee accounting**:

### 📊 Fee Schedule
- **Binance Spot Taker Fee:** `0.10%`
- **Binance USDⓈ-M Futures Taker Fee:** `0.05%`
- **Binance Internal Transfers:** `0.00%` (Free)

### 💰 Automatic Balance Deduction Flow
1. **Ticket Preview:** Displays estimated fee in USDT and percentage rate.
2. **Total Cash Required:** Computes $\text{Total Deduction} = \text{Margin Required} + \text{Estimated Fee}$.
3. **Execution:** Upon confirmation, `Total Deduction` is immediately deducted from liquid cash (`self.cash_usd`) and available USDT holdings (`holdings["USDT"]["free"]`).
4. **Position Close:** Closing fees and realized PnL are added/subtracted, and net proceeds return to liquid cash.

---

## 8. On-Demand AI Execution Control ("Stop Execution")

While commanding the AI agent, the user has **100% control** over in-flight cognitive processing:

- **Thinking Card Stop Button:** When the AI displays `SYRAX AI AGENT THINKING`, a prominent red `⏹️ Stop Execution` button appears in the header.
- **Transforming Input Button:** The input bar's `Execute` button automatically morphs into a pulsing red `⏹️ Stop` button during execution.
- **AbortController Network Cancellation:** Clicking Stop instantly aborts the underlying HTTP request via `AbortController.abort()`, halts backend processing, resets the loading UI, and displays:  
  `🛑 AI Agent execution stopped by user. Ongoing cognitive analysis was aborted safely. No trades were placed or funds modified.`

---

## 9. 24/7 Security Sentry & Post-Trade Guardian

### 🛡️ 24/7 Sentry Exploit Radar (`agent/sentry_agent.py`)
- Real-time radar monitoring bridge hacks, token exploits, flash loan vulnerabilities, and contract deprecations.
- Categorized feeds with threat severity indicators (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- Live market confirmation tag verifying on-chain activity.

### 💂 Post-Trade Guardian (`agent/guardian.py`)
- Actively tracks all ongoing derivative and spot positions.
- **Maximum Adverse Excursion (MAE) Alerts:** Warns if price approaches stop-loss threshold.
- **Trailing Stop Loss Tracker:** Calculates dynamic trailing stops to lock in unrealized profits.
- **Emergency Capital Defense:** Allows 1-click liquidation of vulnerable positions back to liquid USDT.

---

## 10. Autonomous Event-Driven Order Fill Simulator

For pending Limit Orders placed in the sub-wallet:
- **Limit Order Reservation:** Quotes (USDT for buys) or base tokens (for sells) are locked in reserve upon placement.
- **Interactive Simulated Fills:** Traders can test discrete orderbook fill events at **25%, 50%, 75%, or 100%** lot sizes directly from the UI.
- **Deterministic Fill Calculations:** Realistically calculates partial average fill prices, remaining quantities, and proportional fee deductions.
- **Cancel Remainder:** Canceling a pending or partially filled order instantly unlocks the remaining un-filled margin back into liquid cash.

---

## 11. Complete Frontend UI & Navigation Tour (7 Main Views)

SYRAX features a modern, ultra-responsive dark cyberpunk trading terminal built with **Next.js 14, React, Tailwind CSS, Lucide Icons, and Framer Motion animations**.

### 🖥️ Header Navigation Bar
- **Branding:** `SYRAX` — Powered by Binance Agent OS & Google Gemini.
- **Live Ticker Stream:** Real-time animated ticker bar showing 24h price changes for major Binance pairs.
- **Binance MCP Status Pill:** Live indicator showing `● MCP CONNECTED` or `○ SIMULATED / DEMO MODE`.
- **Global Actions:**
  - 🔄 `Internal Transfer` shortcut modal.
  - 🛡️ `Trading Rules & Mandate` configuration modal.
  - 🔶 `Binance MCP Connection` settings modal.
  - 📡 `24/7 Post-Trade Guardian` live status badge.

---

### 📑 The 7 Core Views

#### 1. `Agent Command Center` (Primary View)
- **Natural Language Interaction:** Full conversational chat terminal with multi-turn support.
- **Quick Intent Pills:** 1-click prompt starters (`🚀 Buy $5 PUMP on spot`, `⚡ 10x Long BTC`, `📊 Show my token holdings`, `🛡️ Check Hack & Exploit Risk`, `⚖️ Rebalance Portfolio`, `💵 Consolidate Idle Stablecoins`, `🚨 Emergency Protect`).
- **Dynamic Reasoning Stages:** Animated loading indicator showing the 4 cognitive checkpoints during execution.
- **On-Demand Stop Execution:** Red Stop buttons in both the thinking card and input bar.
- **Inline Cryptographic Order Tickets:** Beautiful order cards with live countdown timers, fee breakdown, total balance deduction, copyable confirm commands, and 1-click confirm/cancel buttons.
- **Inline Execution Receipts:** Green verified stamps for filled orders showing transaction hash, trade ID, and compliance status.
- **Cognitive Verification Traces:** Collapsible inspection drawer detailing Risk Check, Sentry Radar, and Binance Depth checkpoints.

#### 2. `Positions & Sub-Wallet` (Sub-Account Dashboard)
- **5-Wallet Ecosystem Grid:** Visual cards for Spot, Funding, USDT-M Futures, Coin-M Futures, and Margin wallets.
- **Interactive Asset Drawer:** Click any wallet card to view detailed free vs. locked token breakdown and USD valuations.
- **Global All Tokens Matrix:** Complete table of all assets owned across all 5 wallets.
- **Today's PnL Telemetry:** Realized PnL, Unrealized PnL, Fees paid, and daily percentage change.
- **Ongoing Trades Table:**
  - Symbol, Market Type (Spot/Futures), Leverage, Side, Entry Price, Mark Price, Position Value, Unrealized PnL.
  - 🎛️ **Adjust TP/SL:** Modal to modify active trade exit targets.
  - ❌ **Close Position:** 1-click market exit returning margin + net profit to liquid cash.
- **Pending Limit Orders Table:**
  - Limit Price, Distance to Market (%), Reserved Margin, Fill Progress Bar.
  - ⚡ **Simulate Fill:** Buttons to execute 25%, 50%, 75%, or 100% orderbook fills.
  - 🗑️ **Cancel Order:** Release reserved funds back to available cash.
- **Asset Holdings Table:** Free vs Locked token balances with 1-click **Sell to USDT** execution.

#### 3. `Trade History`
- Searchable and filterable ledger of all historical trades, spot liquidations, closed derivative positions, and conversions.
- Displays timestamps, realized PnL in dollars, exact transaction fees paid, and exit reasons.

#### 4. `Market Discovery & Scanner`
- Live market scanner categorized by `ALL`, `FUTURES`, `ALPHA GEMS`, and `SPOT`.
- **Search Bar:** Query any Binance trading pair in real time.
- **Metrics:** 24h Volume, 24h Price Change, Spread (bps), Liquidity Rating, AI Score, Sparkline chart.
- **Action:** 1-click `Generate Ticket` opens the trade ticket generator for that asset.

#### 5. `Security & Sentry Radar`
- Real-time stream of security threat intelligence from the Sentry Agent.
- Displays Threat Title, Affected Token, Severity Badge, Source Credibility, Market Confirmation, and AI Defense Recommendation.

#### 6. `Audit Journal & Cognitive Trace`
- Chronological journal entries of every decision made by the agent (`TRADE`, `WAIT`, `NO TRADE`, `PROTECT`).
- Records entry price, stop-loss, take-profit, risk amount, and full technical reasoning context.

#### 7. `Post-Trade Guardian`
- Live monitoring panel for open trade safety.
- Displays Maximum Adverse Excursion (MAE), Trailing Stop distances, incident history, and emergency de-risking triggers.

---

## 12. Interactive Modals & Settings Control

### 1. `InternalTransferModal`
- Allows instant transfer of USDT or other assets between any of the 5 active Binance wallets.
- Shows available source balance, instant "MAX" button, and confirmation receipt.

### 2. `AdjustTradeModal`
- Allows the trader to adjust Stop-Loss and Take-Profit prices for active ongoing positions.
- Dynamically recalculates new risk bounds to ensure mandate compliance.

### 3. `TradingRulesModal`
- Modify core mandate settings:
  - Total Allocated Capital ($)
  - Maximum Risk Percentage per Trade (default: 1.0%)
  - Maximum Order Size ($)
  - Maximum Permissible Leverage (1x–10x)
  - Require Mandatory Stop Loss (Toggle)
  - Sentry Exploit Filter (Toggle)
  - Target Asset Allocation percentages (USDT, BTC, ETH, SOL, USDC)

### 4. `BinanceMCPModal`
- Connect or disconnect the official **Binance Agent OS MCP Client**.
- Enter Auth Token, Sub-Account ID, and Endpoint URL.
- 1-Click Binance OAuth authorization initiation.

### 5. `NewTradeModal`
- Manual trade creator with real-time risk calculations, leverage sliders, and stop-loss visualizers.

---

## 13. Comprehensive Backend REST & MCP API Reference

The backend runs on **FastAPI (port 8001)** and exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Natural language command endpoint with Gemini cognitive orchestration |
| `GET` | `/api/dashboard` | Consolidated telemetry (Portfolio, Today PnL, Ongoing Trades, Sentry) |
| `GET` | `/api/market/scan` | Live Binance market scanner with AI scoring and tradeability labels |
| `GET` | `/api/market/symbol/{sym}` | Deep orderbook depth and market analysis for a specific symbol |
| `GET` | `/api/subwallet` | Sub-wallet holdings, ongoing trades, pending orders, and cash reserves |
| `POST` | `/api/subwallet/order` | Place immediate market order in sub-wallet |
| `POST` | `/api/subwallet/limit-order` | Place limit order with deterministic margin reservation |
| `POST` | `/api/subwallet/order/simulate-fill` | Simulate partial or full fill (25%, 50%, 75%, 100%) on pending order |
| `POST` | `/api/subwallet/order/cancel` | Cancel pending order and release reserved funds |
| `POST` | `/api/subwallet/trade/close` | Close ongoing trade, calculate realized PnL, deduct closing fee |
| `POST` | `/api/subwallet/trade/update` | Update Stop Loss and Take Profit levels for an open trade |
| `POST` | `/api/subwallet/sell-holding` | Liquidate spot token balance to USDT on Binance Spot |
| `GET` | `/api/subwallet/trades/history` | Historical log of all filled orders, sales, and closed trades |
| `GET` | `/api/subwallet/today-pnl` | Detailed breakdown of today's realized PnL, unrealized PnL, and fees |
| `GET` | `/api/wallets/summary` | 5-Wallet Binance ecosystem balances and token breakdowns |
| `POST` | `/api/wallets/transfer` | Execute zero-fee internal transfer between Binance wallets |
| `GET` | `/api/wallets/transfers` | History of all internal wallet transfers |
| `GET` | `/api/ticket/{id}` | Retrieve OrderTicket metadata, remaining TTL, and status |
| `POST` | `/api/ticket/confirm` | Confirm and atomically execute OrderTicket via confirmation token |
| `POST` | `/api/ticket/cancel` | Cancel pending OrderTicket |
| `GET` | `/api/tickets/pending` | List all active unconfirmed order tickets |
| `GET` | `/api/rules` | Fetch active user trading mandate rules and available cash |
| `POST` | `/api/rules` | Update trading mandate rules and target allocations |
| `GET` | `/api/sentry` | Active security events from the 24/7 Sentry Radar |
| `GET` | `/api/journal` | Complete cognitive audit journal entries |
| `GET` | `/api/monitor/status` | Autonomous background monitoring daemon status |
| `POST` | `/api/monitor/toggle` | Start or pause the autonomous monitoring daemon |
| `GET` | `/api/guardian/status` | Live status of the Post-Trade Guardian |
| `GET` | `/api/guardian/incidents` | Incident logs recorded by Post-Trade Guardian |
| `POST` | `/api/guardian/config` | Update Guardian sensitivity and trailing stop rules |
| `GET` | `/api/binance/mcp/status` | Connection status of the Binance Agent OS MCP Client |
| `POST` | `/api/binance/mcp/connect` | Connect to Binance Agent OS MCP Server |
| `POST` | `/api/binance/mcp/disconnect`| Disconnect from Binance Agent OS MCP |
| `GET` | `/api/binance/oauth/initiate`| Generate Binance OAuth authorization URL |
| `GET` | `/mcp/sse` | **SYRAX MCP Server** Server-Sent Events endpoint (14 exposed agent tools) |
| `POST` | `/mcp/messages` | **SYRAX MCP Server** tool execution gateway for Claude/Cursor/Antigravity |

---

## 14. How to Run & Deploy

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Windows / Linux / macOS

### 1. Start the FastAPI Backend
```bash
# Navigate to project root
cd syrax

# Activate virtual environment
venv\Scripts\activate   # (Windows)
# source venv/bin/activate  (Linux/Mac)

# Install requirements
pip install -r requirements.txt

# Start FastAPI server on port 8001
uvicorn backend.main:app --port 8001 --reload
```
*Backend runs at:* `http://127.0.0.1:8001`  
*Interactive Swagger API Docs:* `http://127.0.0.1:8001/docs`

---

### 2. Start the Next.js Frontend
```bash
# Navigate to frontend directory
cd syrax/frontend

# Install dependencies
npm install

# Start Next.js development server on port 3001
npm run dev -- -p 3001
```
*Frontend runs at:* `http://localhost:3001`

---

## 15. Summary Checklist of Project Capabilities

| Capability | Status | Details |
|---|:---:|---|
| **Google Gemini Natural Language Agent** | ✅ Complete | Multilingual, multi-intent conversational command parsing |
| **Strict 1.0% Max Loss Mandate** | ✅ Complete | Mathematically enforced on every trade ($5 max loss on $500 base) |
| **Mandatory Stop-Loss Gating** | ✅ Complete | Zero trades permitted without verified Stop Loss |
| **Two-Phase Cryptographic Order Tickets** | ✅ Complete | SHA-256 Checksum, 120s live TTL, `CONFIRM PO-XXXXXX` token |
| **On-Demand Stop Execution Button** | ✅ Complete | Instant cancellation of in-flight AI reasoning via `AbortController` |
| **5-Wallet Binance Ecosystem** | ✅ Complete | Spot, Funding, USD-M Futures, Coin-M Futures, Margin (Earn excluded) |
| **Zero-Fee Internal Transfers** | ✅ Complete | 1-Click instant asset movement across all 5 wallets |
| **Interactive Token Balance Drawer** | ✅ Complete | Free vs Locked token balances with live USD valuations |
| **Exact Fee Deduction Engine** | ✅ Complete | 0.10% Spot / 0.05% Futures taker fees deducted with margin |
| **Event-Driven Fill Simulator** | ✅ Complete | Test partial & full fills (25%, 50%, 75%, 100%) on pending orders |
| **24/7 Sentry Exploit Radar** | ✅ Complete | Continuous scanning for bridge hacks, smart contract bugs, depegs |
| **Post-Trade Guardian** | ✅ Complete | Adverse excursion tracking, trailing stop alerts, emergency liquidation |
| **Binance Agent OS MCP Integration** | ✅ Complete | Official MCP Client connection + Native SYRAX MCP Server (14 tools) |
| **7 Fully Realized UI Views** | ✅ Complete | Command Center, Positions, History, Scanner, Sentry, Journal, Guardian |

---
*Created for the Binance Agent OS Hackathon.*  
*Repository Root: `C:\Users\UMMEA SAWDA SRUTI\.gemini\antigravity\scratch\syrax`*
