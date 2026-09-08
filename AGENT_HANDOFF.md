# SYRAX — Agent Handoff & Continuity Guide

> **To the Incoming Antigravity Agent:**
> Welcome to **SYRAX**. This guide provides exact instructions for maintaining and extending the codebase without introducing regressions or altering approved architectures.

---

### 1. How to Continue This Project
1. **Understand the Codebase Location**:
   - Workspace root: `C:\Users\UMMEA SAWDA SRUTI\.gemini\antigravity\scratch\syrax`
   - Python Virtual Environment: `venv\Scripts\python.exe`
   - Node.js environment: `C:\Program Files\nodejs`
2. **Review Project Context**:
   - Read `PROJECT_CONTEXT.md` and `DEVELOPMENT_STATUS.md` first.
3. **Verify Running Servers**:
   - FastAPI Backend: `http://127.0.0.1:8001`
   - Next.js Frontend: `http://127.0.0.1:3001`
4. **Communicate with the User**:
   - The user speaks Bengali / Banglish (e.g. `5$ worth of pump kinte`, `eita update koro`).
   - Provide conversational responses in Bengali; keep code, technical terms, UI labels, and terminal outputs in English.

---

### 2. What You Must NOT Change Unnecessarily

1. **DO NOT change the core multi-agent architecture**:
   - `SyraxOrchestrator` coordinates `MarketAgent`, `RiskEngine`, `NewsSentryAgent`, `PortfolioAgent`, and `AIClient`. Do not collapse or rewrite this pipeline.
2. **DO NOT auto-set Take-Profit (TP)**:
   - Take-Profit must **NEVER** be automatically calculated or injected on user buy/sell commands unless the user explicitly requested a TP level (e.g., `TP 120` or `take profit at 150`).
3. **DO NOT remove token existence verification**:
   - Every user trade command must validate the token against Binance live ticker data before execution. If the token is not live on Binance Spot or Futures, abort trade with `NO TRADE` and prompt the user for clarification.
4. **DO NOT remove Stop-Loss safeguards**:
   - The Risk Engine strictly enforces that risk per trade does not exceed 1% of sub-wallet capital. Mandatory stop-loss must always be active.
5. **DO NOT hardcode API keys or secrets in source files**:
   - All credentials must be loaded via `os.getenv` from `.env`. Never commit secrets.

---

### 3. Current Architecture & Key File Map

| Component | File Path | Responsibilities |
| :--- | :--- | :--- |
| **API Server** | `backend/main.py` | FastAPI application, REST endpoints (`/api/chat`, `/api/subwallet`, `/api/rules`, etc.), startup sentinel hooks. |
| **Sub-Wallet** | `backend/binance/sub_wallet.py` | Quarantined $500 balance manager, position tracking (Spot & Futures), trade history receipts, fee accounting. |
| **Binance Bridge** | `backend/binance/agent_os.py` | Real-time Binance REST client (`api.binance.com`), HMAC signing for testnet, ticker caching. |
| **Sentinel Daemon** | `backend/monitor_daemon.py` | 24/7 background loop inspecting held positions and exploit risks every 15 seconds. |
| **MCP Server** | `backend/mcp_server.py` | FastMCP server exposing native tools over SSE at `/mcp`. |
| **Orchestrator** | `agent/orchestrator.py` | Natural language command parser, token extractor, multi-agent pipeline controller. |
| **AI Client** | `agent/ai_client.py` | OpenRouter / Gemini cognitive adjudication with JSON schema enforcement. |
| **Risk Engine** | `agent/risk_engine.py` | Mathematical 1% risk gatekeeper, position size calculator, invalidation conditions. |
| **News Sentry** | `agent/news_sentry_agent.py` | Exploit radar, news sentiment analyzer, and emergency protection evaluator. |
| **Frontend UI** | `frontend/app/page.tsx` | Main trading dashboard, live price banner, trade history, command bar, rules drawer. |
| **Frontend API** | `frontend/lib/api.ts` | TypeScript HTTP client communicating with backend port 8001. |

---

### 4. Coding Conventions & Best Practices

1. **Python Backend**:
   - Asynchronous I/O with `async`/`await` for all network calls.
   - Use `httpx.AsyncClient` for external API queries with explicit timeouts.
   - Safe dictionary iteration: use `list(dict.keys())` when iterating over structures that could change during execution.
   - Guard against `NoneType` formatting: when `take_profit` or `stop_loss` is optional, use conditional checks before string formatting (`f"${val:,.2f}" if val is not None else "None"`).
2. **Frontend Next.js**:
   - Client components tagged with `'use client'`.
   - Polling intervals with safety cleanup in `useEffect`.
   - Display both Spot and Futures positions with explicit tags and color badges (`SPOT` in blue/emerald, `FUTURES` in purple/amber).
   - Show complete trade execution details (Order ID, fee breakdown, entry, SL, TP).

---

### 5. Important Safety & Compliance Rules

1. **Capital Quarantine**: All agent activity is confined to the Sub-Wallet ($500 initial budget). The main exchange balance is never exposed directly.
2. **Maximum Loss Ceiling**: Maximum loss per single trade is capped at 1.0% ($5.00 on a $500 wallet).
3. **Anti-Hallucination Gate**: If the token symbol extracted from user text cannot be verified against Binance markets, execution is blocked immediately with a helpful clarification request.
4. **Emergency Sentry**: If a critical exploit or hack is verified for a token in the portfolio, the sentinel triggers `PROTECT` mode, closing or hedging exposure.

---

### 6. Planned Integrations

#### A. Direct Google Gemini SDK Integration
- Current: Uses OpenRouter API with Gemini models (`google/gemini-2.0-flash-exp:free`).
- Plan: Install `google-genai` and support direct `GEMINI_API_KEY` authentication for ultra-low-latency multimodal analysis and real-time audio chat.

#### B. Binance Agent OS & MCP Ecosystem
- Current: Full tool contracts implemented in `backend/mcp_server.py` and `backend/binance/agent_os.py`.
- Plan: Register SYRAX in the official Binance Agent OS registry for interoperability with other trading agents.

#### C. News & Exploit Sentinel Expansion
- Current: Live news simulation and radar feed.
- Plan: Connect to live RSS/WebSocket feeds from CryptoPanic, Coindesk, and PeckShield security alerts.

#### D. Deployment & Demo
- Local ports: Frontend `3001`, Backend `8001`.
- Production build: `npm run build` verified in `frontend/`.
