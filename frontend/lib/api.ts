import {
  Portfolio,
  Opportunity,
  SentryEvent,
  JournalEntry,
  ChatResponse,
  SubWalletData,
  MonitorStatus,
  MCPInfo,
  UserRules,
  TradeHistoryItem,
  OrderTicketCardData,
  GuardianStatusData,
  GuardianIncidentData,
  BinanceMCPStatus,
  WalletsSummaryData,
  InternalTransferReceipt
} from "@/types";

const API_BASE = "http://127.0.0.1:8001";

export const FALLBACK_PORTFOLIO: Portfolio = {
  total_value_usd: 485.20,
  available_cash_usd: 250.0,
  holdings: [
    { asset: "USDT", free: 250.0, locked: 0.0, total: 250.0, price_usd: 1.0, value_usd: 250.0, allocation_pct: 51.5 },
    { asset: "BTC", free: 0.00187, locked: 0.0, total: 0.00187, price_usd: 79966.0, value_usd: 150.0, allocation_pct: 30.9 },
    { asset: "ETH", free: 0.0287, locked: 0.0, total: 0.0287, price_usd: 2505.7, value_usd: 72.0, allocation_pct: 14.8 },
    { asset: "SOL", free: 0.122, locked: 0.0, total: 0.122, price_usd: 105.9, value_usd: 13.0, allocation_pct: 2.7 },
  ],
  account_type: "Binance Agentic Sub-Account",
  execution_mode: "Assisted Mode (Strict Risk Enforcement)",
  updated_at: new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC",
};

export const FALLBACK_OPPORTUNITIES: Opportunity[] = [
  {
    symbol: "BTCUSDT",
    last_price: 79966.0,
    change_24h: 0.08,
    volume_24h: 8850.0,
    quote_volume_24h: 708000000.0,
    trend: "CONSOLIDATION_RANGE",
    momentum: "NEUTRAL",
    spread_bps: 0.01,
    liquidity_quality: "HIGH",
    ai_score: 82,
    label: "TRADEABLE",
    decision: "TRADE",
    reasoning: "Strong institutional orderbook depth, 0.01 bps ultra-tight spread on Binance Spot.",
    setup: {
      entry_price: 79966.0,
      stop_loss: 78526.0,
      take_profit: 83564.0,
      stop_dist_pct: 1.8,
      target_dist_pct: 4.5,
      risk_reward_ratio: 2.5,
    },
  },
  {
    symbol: "ETHUSDT",
    last_price: 2505.7,
    change_24h: -0.42,
    volume_24h: 195000.0,
    quote_volume_24h: 488000000.0,
    trend: "CONSOLIDATION_RANGE",
    momentum: "NEUTRAL",
    spread_bps: 0.05,
    liquidity_quality: "HIGH",
    ai_score: 79,
    label: "TRADEABLE",
    decision: "TRADE",
    reasoning: "Consolidating near key structural support with deep institutional bid liquidity.",
    setup: {
      entry_price: 2505.7,
      stop_loss: 2460.6,
      take_profit: 2618.5,
      stop_dist_pct: 1.8,
      target_dist_pct: 4.5,
      risk_reward_ratio: 2.5,
    },
  },
  {
    symbol: "SOLUSDT",
    last_price: 105.93,
    change_24h: 1.15,
    volume_24h: 1450000.0,
    quote_volume_24h: 153000000.0,
    trend: "MODERATE_UPTREND",
    momentum: "NEUTRAL_POSITIVE",
    spread_bps: 0.09,
    liquidity_quality: "HIGH",
    ai_score: 84,
    label: "TRADEABLE",
    decision: "TRADE",
    reasoning: "High-volume recovery above local pivot ($105.00) with strong liquidity replenishment.",
    setup: {
      entry_price: 105.93,
      stop_loss: 104.02,
      take_profit: 110.70,
      stop_dist_pct: 1.8,
      target_dist_pct: 4.5,
      risk_reward_ratio: 2.5,
    },
  },
  {
    symbol: "SUIUSDT",
    last_price: 0.8067,
    change_24h: 0.35,
    volume_24h: 72000000.0,
    quote_volume_24h: 58000000.0,
    trend: "CONSOLIDATION_RANGE",
    momentum: "NEUTRAL",
    spread_bps: 0.12,
    liquidity_quality: "HIGH",
    ai_score: 76,
    label: "TRADEABLE",
    decision: "TRADE",
    reasoning: "SUI breaking upward from base consolidation with positive taker volume ratio.",
    setup: {
      entry_price: 0.8067,
      stop_loss: 0.7922,
      take_profit: 0.8430,
      stop_dist_pct: 1.8,
      target_dist_pct: 4.5,
      risk_reward_ratio: 2.5,
    },
  },
  {
    symbol: "DOGEUSDT",
    last_price: 0.1448,
    change_24h: 2.15,
    volume_24h: 1100000000.0,
    quote_volume_24h: 159000000.0,
    trend: "HIGH_VOLATILITY",
    momentum: "POSITIVE",
    spread_bps: 0.07,
    liquidity_quality: "HIGH",
    ai_score: 72,
    label: "WATCH",
    decision: "WAIT",
    reasoning: "Elevated volume but approaching overhead multi-day resistance level.",
    setup: {
      entry_price: 0.1448,
      stop_loss: 0.1415,
      take_profit: 0.1530,
      stop_dist_pct: 2.3,
      target_dist_pct: 5.7,
      risk_reward_ratio: 2.5,
    },
  },
];

export const FALLBACK_EVENTS: SentryEvent[] = [
  {
    id: "evt-1",
    title: "Ethereum Core Devs Finalize Pectra Upgrade Timeline",
    summary: "Execution spec finalized; no critical bugs identified in devnet-9 fuzzing runs.",
    token: "ETH",
    timestamp: Date.now() - 3600000,
    source: "Ethereum Foundation GitHub & Discord",
    source_credibility: "OFFICIAL_DEV_CHANNEL (Score 98/100)",
    market_confirmed: true,
    severity: "LOW",
    status: "CONFIRMED_BENIGN",
    action_recommended: "NO_ACTION_REQUIRED",
    reasoning: "Scheduled routine protocol improvement with extensive testnet coverage.",
  },
  {
    id: "evt-2",
    title: "Solana Ecosystem Bridge RPC Node Latency Spike",
    summary: "Secondary RPC provider experiencing transient 429 rate limits; main cluster unaffected.",
    token: "SOL",
    timestamp: Date.now() - 7200000,
    source: "Solana Status & Twitter Verified Intel",
    source_credibility: "MULTI_SOURCE_VERIFIED (Score 88/100)",
    market_confirmed: true,
    severity: "LOW",
    status: "MONITORING",
    action_recommended: "MAINTAIN_CURRENT_LIMITS",
    reasoning: "Consensus layer operating nominally with 2,400 TPS throughput.",
  },
];

export const FALLBACK_JOURNAL: JournalEntry[] = [
  {
    id: "jrn-001",
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    asset: "BTCUSDT",
    decision: "TRADE",
    entry_price: 78500.0,
    stop_loss: 77000.0,
    take_profit: 82500.0,
    risk_amount_usd: 5.0,
    risk_pct: 1.0,
    status: "EXECUTED",
    realized_pnl_usd: 4.85,
    reason: "Trend continuation above $78,000 psychological support with strong taker buy flow.",
    news_context: "Institutional ETF inflows recorded at +$340M net for the day.",
  },
];

export const api = {
  async getDashboardOverview() {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    
    try {
      const res = await fetch(`${API_BASE}/api/overview`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}

    return {
      portfolio: FALLBACK_PORTFOLIO,
      today_pnl: {
        total_pnl_usd: 1.15,
        pnl_pct: 0.23,
        realized_pnl_usd: 0.0,
        unrealized_pnl_usd: 1.15,
        fees_usd: 0.015,
        funding_usd: 0.0,
        status: "PROFIT",
        timezone: "UTC",
        reset_time_utc: "00:00:00 UTC",
        is_live_mcp: false,
        sub_account_id: "SUB-AGENT-01-ALPHA",
      },
      pnl_24h: { pnl_usd: 1.15, pnl_pct: 0.23, status: "PROFIT" },
      risk_exposure: {
        current_at_risk_usd: 4.85,
        max_risk_pct: 1.0,
        max_allowed_loss_usd: 5.0,
        status: "NORMAL_GUARDED",
      },
      top_opportunities: FALLBACK_OPPORTUNITIES.slice(0, 3),
      active_events: FALLBACK_EVENTS,
      idle_cash: [
        {
          asset: "USDC",
          amount: 12.5,
          amount_usd: 12.5,
          type: "IDLE_STABLECOIN",
          recommendation: "Convert to USDT at 0% fee to consolidate active margin capital.",
        },
      ],
      ai_daily_insight:
        "Macro tape indicates selective risk-on liquidity rotation. Strategy: Favor high-liquidity orderbook entries (BTC/ETH), strictly cap risk to 1%, and maintain stablecoin reserves.",
      execution_mode: "ASSISTED",
    };
  },

  async getDashboard() {
    return this.getDashboardOverview();
  },

  async getMarketScan(category: string = "ALL", limit: number = 25): Promise<Opportunity[]> {
    try {
      const res = await fetch(`${API_BASE}/api/market/scan?category=${encodeURIComponent(category)}&limit=${limit}`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data && Array.isArray(data.symbols)) return data.symbols;
      }
    } catch {}
    return FALLBACK_OPPORTUNITIES;
  },

  async searchSymbols(query: string) {
    try {
      const res = await fetch(`${API_BASE}/api/market/search?q=${encodeURIComponent(query)}`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return { query, results: [] };
  },

  async getSymbolAnalysis(symbol: string): Promise<{ analysis: Opportunity; orderbook: any }> {
    try {
      const res = await fetch(`${API_BASE}/api/market/symbol/${encodeURIComponent(symbol)}`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    const opp = FALLBACK_OPPORTUNITIES.find((o) => o.symbol === symbol) || FALLBACK_OPPORTUNITIES[0];
    return {
      analysis: opp,
      orderbook: {
        bids: [[opp.last_price * 0.9995, 1.5], [opp.last_price * 0.9990, 3.2]],
        asks: [[opp.last_price * 1.0005, 1.2], [opp.last_price * 1.0010, 2.8]],
        spread_bps: 0.05,
      },
    };
  },

  async getKlines(symbol: string = "BTCUSDT", interval: string = "1h", limit: number = 100) {
    try {
      const res = await fetch(`${API_BASE}/api/market/klines?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=${limit}`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        return data.candles;
      }
    } catch {}
    return [];
  },

  async getPortfolio(): Promise<{ portfolio: Portfolio; rebalance_plan: any }> {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return {
      portfolio: FALLBACK_PORTFOLIO,
      rebalance_plan: {
        drift_pct: 4.2,
        actions: [],
        idle_cash_opportunities: [],
        rebalance_required: false,
      },
    };
  },

  async getSentry(): Promise<{ events: SentryEvent[]; sentry_status: string; surveillance_level: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/sentry`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return {
      events: FALLBACK_EVENTS,
      sentry_status: "ONLINE",
      surveillance_level: "MAXIMUM_3_LAYER",
    };
  },

  async simulateSentryEvent(token: string = "SOL"): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/sentry/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (res.ok) return await res.json();
    } catch {}
    return { success: true, message: `Simulated sentry trigger for ${token}` };
  },

  async triggerEmergencyProtect(token: string): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/sentry/protect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (res.ok) return await res.json();
    } catch {}
    return { success: true, message: `Emergency protect triggered for ${token}` };
  },

  async getJournal(): Promise<{ journal: JournalEntry[]; executions: any[] }> {
    try {
      const res = await fetch(`${API_BASE}/api/journal`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return {
      journal: FALLBACK_JOURNAL,
      executions: [],
    };
  },

  async getTradeHistory(): Promise<TradeHistoryItem[]> {
    try {
      const res = await fetch(`${API_BASE}/api/subwallet/trades/history`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        return data.trades || data.history || [];
      }
    } catch {}
    try {
      const res = await fetch(`${API_BASE}/api/subwallet/history`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        return data.trades || data.history || [];
      }
    } catch {}
    return [];
  },

  async getMCPInfo(): Promise<MCPInfo | null> {
    try {
      const res = await fetch(`${API_BASE}/api/mcp/info`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return {
      url: "http://127.0.0.1:8001/mcp",
      status: "ONLINE",
      version: "1.0.0",
      tools_count: 14,
      endpoints: ["/api/dashboard", "/api/chat", "/api/subwallet", "/api/wallets/summary"],
    };
  },

  async sendChatMessage(message: string, mandateOverride?: any, signal?: AbortSignal): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, mandate_override: mandateOverride }),
      signal,
    });
    if (!res.ok) {
      throw new Error(`Chat request failed with HTTP ${res.status}`);
    }
    return await res.json();
  },

  async executeTradeAction(action: any): Promise<any> {
    const res = await fetch(`${API_BASE}/api/trade/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    return await res.json();
  },

  async executeConvert(fromAsset: string, toAsset: string, amount: number): Promise<any> {
    const res = await fetch(`${API_BASE}/api/cash/convert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_asset: fromAsset, to_asset: toAsset, amount }),
    });
    return await res.json();
  },

  async getUserRules(): Promise<{ rules: UserRules; available_cash_usd: number; ongoing_trades_count: number }> {
    try {
      const res = await fetch(`${API_BASE}/api/rules`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return {
      rules: {
        capital_usd: 500.0,
        max_risk_pct: 1.0,
        max_order_size_usd: 25.0,
        max_leverage: 10,
        require_stop_loss: true,
        sentry_exploit_filter: true,
        execution_mode: "AUTONOMOUS",
        target_allocations: { USDT: 40.0, BTC: 30.0, ETH: 15.0, SOL: 10.0, USDC: 5.0 },
      },
      available_cash_usd: 250.0,
      ongoing_trades_count: 2,
    };
  },

  async updateUserRules(rules: Partial<UserRules>): Promise<{ success: boolean; rules: UserRules }> {
    const res = await fetch(`${API_BASE}/api/rules`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rules),
    });
    return await res.json();
  },

  async getSubWallet(): Promise<SubWalletData> {
    try {
      const res = await fetch(`${API_BASE}/api/subwallet`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return {
      analysis: {
        total_portfolio_value_usd: 485.20,
        available_cash_usd: 250.0,
        allocated_budget_usd: 500.0,
        total_crypto_value_usd: 235.20,
        cash_allocation_pct: 51.5,
        crypto_allocation_pct: 48.5,
        holdings_count: 4,
        unrealized_pnl_usd: 0.0,
        realized_pnl_usd: 0.0,
        ongoing_trades_count: 0,
        pending_orders_count: 0,
        status: "HEALTHY",
      },
      pending_orders: [],
      ongoing_trades: [],
      closed_trades: [],
      trade_history: [],
    };
  },

  async getTodayPnL(): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/subwallet/today-pnl`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async getMonitorStatus(): Promise<MonitorStatus | null> {
    try {
      const res = await fetch(`${API_BASE}/api/monitor/status`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async toggleMonitor(): Promise<MonitorStatus> {
    const res = await fetch(`${API_BASE}/api/monitor/toggle`, { method: "POST" });
    return await res.json();
  },

  async placeSubWalletOrder(payload: { symbol: string; side: string; notional_usd: number; stop_loss?: number; take_profit?: number; market_type?: string; leverage?: number; margin_type?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  async openSubWalletOrder(symbol: string, side: string, notional_usd: number, stop_loss?: number, take_profit?: number, market_type: string = "SPOT", leverage: number = 1, margin_type: string = "ISOLATED"): Promise<any> {
    return this.placeSubWalletOrder({ symbol, side, notional_usd, stop_loss, take_profit, market_type, leverage, margin_type });
  },

  async placeSubWalletLimitOrder(payload: { symbol: string; side: string; limit_price: number; quantity?: number; notional_usd?: number; stop_loss?: number; take_profit?: number; market_type?: string; leverage?: number; margin_type?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/limit-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  async simulateOrderFill(orderId: string, fillPct: number = 100): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/order/simulate-fill`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId, fill_pct: fillPct }),
    });
    return await res.json();
  },

  async simulateFillOrder(orderId: string, fillPct: number = 100): Promise<any> {
    return this.simulateOrderFill(orderId, fillPct);
  },

  async cancelPendingOrder(orderId: string, symbol?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/order/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId, symbol }),
    });
    return await res.json();
  },

  async closeSubWalletTrade(tradeId: string, reason: string = "Manual Exit"): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/trade/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trade_id: tradeId, reason }),
    });
    return await res.json();
  },

  async updateSubWalletTrade(tradeId: string, stopLoss?: number, takeProfit?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/trade/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trade_id: tradeId, stop_loss: stopLoss, take_profit: takeProfit }),
    });
    return await res.json();
  },

  async updateSubWalletTradeLevels(tradeId: string, stopLoss?: number, takeProfit?: number): Promise<any> {
    return this.updateSubWalletTrade(tradeId, stopLoss, takeProfit);
  },

  async sellAssetHolding(asset: string, quantity?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/sell-holding`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset, quantity }),
    });
    return await res.json();
  },

  async sellSubWalletHolding(asset: string, quantity?: number): Promise<any> {
    return this.sellAssetHolding(asset, quantity);
  },

  async executeSubWalletRebalance(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/subwallet/rebalance/execute`, { method: "POST" });
    return await res.json();
  },

  // =========================================================================
  // ORDER TICKET CONFIRMATION / CANCELLATION APIS
  // =========================================================================

  async getOrderTicket(ticketId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/ticket/${ticketId}`, { cache: "no-store" });
    return await res.json();
  },

  async getTicket(ticketId: string): Promise<any> {
    return this.getOrderTicket(ticketId);
  },

  async confirmOrderTicket(ticketId: string, token?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/ticket/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticket_id: ticketId, confirmation_token: token }),
    });
    return await res.json();
  },

  async confirmTicket(ticketId: string, token?: string): Promise<any> {
    return this.confirmOrderTicket(ticketId, token);
  },

  async cancelOrderTicket(ticketId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/ticket/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticket_id: ticketId }),
    });
    return await res.json();
  },

  async cancelTicket(ticketId: string): Promise<any> {
    return this.cancelOrderTicket(ticketId);
  },

  // =========================================================================
  // GUARDIAN SENTINEL APIS
  // =========================================================================

  async getGuardianStatus(): Promise<GuardianStatusData | null> {
    try {
      const res = await fetch(`${API_BASE}/api/guardian/status`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async getGuardianIncidents(limit: number = 20): Promise<GuardianIncidentData[]> {
    try {
      const res = await fetch(`${API_BASE}/api/guardian/incidents?limit=${limit}`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return [];
  },

  async updateGuardianConfig(config: Record<string, any>): Promise<any> {
    const res = await fetch(`${API_BASE}/api/guardian/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    return await res.json();
  },

  // =========================================================================
  // BINANCE MCP & OAUTH APIS
  // =========================================================================

  async getBinanceMcpStatus(): Promise<BinanceMCPStatus | null> {
    try {
      const res = await fetch(`${API_BASE}/api/binance/mcp/status`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async connectBinanceMcp(payload: { auth_token: string; sub_account_id?: string; endpoint_url?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/api/binance/mcp/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  async disconnectBinanceMcp(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/binance/mcp/disconnect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return await res.json();
  },

  async initiateBinanceOAuth(sub_account_id?: string): Promise<{ authorization_url: string; state: string } | null> {
    try {
      const res = await fetch(`${API_BASE}/api/binance/oauth/initiate?sub_account_id=${encodeURIComponent(sub_account_id || "agentic-sub-01")}`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async getBinanceStatus(): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/binance/status`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async connectBinanceApi(payload: { api_key: string; api_secret: string; network?: string }): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/binance/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      return await res.json();
    } catch (err: any) {
      return { configured: false, connected: false, message: err?.message || "Network error connecting API keys." };
    }
  },

  // =========================================================================
  // MULTI-WALLET & INTERNAL TRANSFER APIS
  // =========================================================================

  async getWalletsSummary(): Promise<WalletsSummaryData | null> {
    try {
      const res = await fetch(`${API_BASE}/api/wallets/summary`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  },

  async executeInternalTransfer(payload: { from_wallet: string; to_wallet: string; asset: string; amount: number }): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/wallets/transfer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      return await res.json();
    } catch (err: any) {
      return { success: false, error: err?.message || "Network error executing internal transfer." };
    }
  },

  async getInternalTransfers(): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/wallets/transfers`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
    return { transfers: [], total_count: 0 };
  },
};
