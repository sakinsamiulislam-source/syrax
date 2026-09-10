# 🦅 SYRAX: Institutional-Grade Autonomous Crypto AI Trading Agent

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2+-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Interactions%20API-4285F4?style=flat&logo=google&logoColor=white)](https://aistudio.google.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SYRAX** is an institutional-grade, multi-agent cryptocurrency trading terminal and execution gateway powered by **Google Gemini**. It bridges cutting-edge LLM market reasoning with deterministic risk management, real-time liquidity analytics, and a Human-in-the-Loop (HITL) cryptographic order verification workflow.

---

## 🏛️ System Architecture

```
                                  ┌─────────────────────────────┐
                                  │      TRADER INTERFACE       │
                                  │  (Next.js 14 Command Center)│
                                  └──────────────┬──────────────┘
                                                 │ Natural Language / Multilingual
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │  SEMANTIC INTENT ROUTER     │
                                  │  (Semantic Brain & Mandates)│
                                  └──────────────┬──────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
   ┌──────────────────────────────┐ ┌──────────────────────────────┐ ┌──────────────────────────────┐
   │    MARKET SCANNER AGENT      │ │     RISK SENTRY & RADAR      │ │    MULTI-WALLET LEDGER       │
   │  * Live Binance Tickers      │ │  * 24/7 Threat Sentinel      │ │  * Spot, Margin, Futures,    │
   │  * Funding Rates & Spreads   │ │  * 1.0% Risk Caps            │ │    Funding Sub-Wallets       │
   │  * Multi-Factor Alpha Score  │ │  * Max Drawdown Guards       │ │  * Atomic Internal Transfers │
   └──────────────┬───────────────┘ └──────────────┬───────────────┘ └──────────────┬───────────────┘
                  │                                │                                │
                  └────────────────────────────────┼────────────────────────────────┘
                                                   │
                                                   ▼
                                  ┌─────────────────────────────┐
                                  │ DETERMINISTIC GATEWAY (HITL)│
                                  │  * SHA-256 Exact Tickets    │
                                  │  * 120s TTL Invalidation    │
                                  │  * Automated Fee Settlement │
                                  └─────────────────────────────┘
```

---

## ✨ Key Features

### 🧠 1. Cognitive Multi-Agent Engine
- **Intent Router & Semantic Brain:** Directs user queries into specialized execution mandates (*Opportunity Discovery*, *Portfolio Risk Audit*, *Order Proposal*, or *Exploratory Q&A*). Supports fluent natural language in both English and Banglish.
- **Dynamic Reasoning Tracing:** Transparent cognitive verification checkpoints displayed in real time.

### ⚡ 2. Real-Time Market Intelligence
- **High-Conviction Scanning:** Continually tracks order book depth, 24h trading volumes, bid-ask spreads (bps), and funding rates across top cryptocurrencies (BTC, ETH, SOL, BNB, etc.).
- **Institutional Setup Scoring:** Evaluates tradeable setups complete with mathematically defined Entry, Mandatory Stop-Loss, Take-Profit targets, and Risk-to-Reward (R:R) ratios.

### 🛡️ 3. 24/7 Autonomous Risk Sentry & Guardian
- **Portfolio Health Sentinel:** Continuous background daemon monitoring overall equity and drawdown.
- **Strict Guardrails:** Enforces a 1.0% portfolio risk cap per trade, dynamic trailing stops, and automatic trading halts upon breach of maximum drawdown thresholds.
- **Sentry Threat Radar:** Real-time DEFCON threat evaluation analyzing macro events, network congestion, and volatility spikes.

### 📜 4. Exact Order Tickets (Human-in-the-Loop)
- **Zero Hallucinated Executions:** Orders are not placed directly by the LLM. Instead, the agent drafts an **Exact Order Ticket** containing an immutable SHA-256 verification hash, active 120s expiration window, and explicit trading fee calculation.
- **Deterministic Settlement:** Executed only when explicitly confirmed (`CONFIRM <TICKET_ID>`), deducting cash and taker fees from the respective sub-wallet.

### 💼 5. Isolated Multi-Wallet Architecture
- **Sub-Wallet Segregation:** Dedicated sub-wallets for **Spot**, **Margin**, **Futures**, and **Funding**.
- **Atomic Capital Transfers:** Effortlessly rebalance capital across accounts without external counterparty risk.

---

## 🚀 Quick Start & Installation Guide

### Prerequisites
- **Git** (>= 2.30)
- **Python** (>= 3.10)
- **Node.js** (>= 18.x) & **npm**
- **Google Gemini API Key** ([Get free key here](https://aistudio.google.com))

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/sakinsamiulislam-source/syrax.git
cd syrax
```

---

### Step 2: Backend Setup (FastAPI & Gemini Engine)

1. **Create and activate a Python virtual environment:**
   - **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY="your_actual_gemini_api_key_here"
   ```

4. **Launch FastAPI server:**
   ```bash
   uvicorn backend.main:app --port 8001 --reload
   ```
   *The backend will be live at `http://127.0.0.1:8001`.*

---

### Step 3: Frontend Setup (Next.js 14 Terminal)

Open a **new terminal window** and run:
```bash
cd syrax/frontend
npm install
npm run dev -- -p 3001
```
*The interactive trading terminal UI will be live at `http://localhost:3001`.*

---

## 💬 Interacting with SYRAX

Open `http://localhost:3001` in your browser and try the following prompts in the **Agent Command Center**:

| Objective | Example Prompt | Description |
| :--- | :--- | :--- |
| **Market Discovery** | *"Find the most interesting tradeable opportunities right now, prioritizing liquidity and controlled risk."* | Scans multi-asset order books, funding rates, and spreads for high-conviction setups. |
| **Risk Audit** | *"What is the biggest risk in my portfolio right now?"* | Audits portfolio health, margin utilization, liquid cash, and Sentry threat levels. |
| **Order Proposal** | *"Propose a $20 buy order for SOL with strict stop loss."* | Generates a cryptographically hashed, fee-accounted **Exact Order Ticket**. |
| **Execution** | `CONFIRM PO-E49AA6` | Validates through Safety Gatekeeper and executes order settlement. |

---

## 🛠️ Tech Stack

- **AI Core:** Google Gemini Models via Google GenAI SDK
- **Backend Framework:** FastAPI, Uvicorn, Pydantic, HTTPX, Python Dotenv
- **Frontend Framework:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide React
- **Market Feeds:** Real-time Binance Public API integrations
- **Data Persistence:** Lightweight JSON State Engine & In-Memory Ledgers

---

## 🔒 Security & Risk Disclaimer

*SYRAX is designed as an advanced AI trading simulation and institutional workflow framework. All live orders and simulations should be thoroughly tested with paper trading before deploying capital to live production exchange keys.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).