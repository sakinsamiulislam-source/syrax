"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Terminal,
  Activity,
  PieChart,
  Clock,
  TrendingUp,
  AlertTriangle,
  BookOpen,
  Info,
  DollarSign,
  Zap,
  Shield,
  Radio,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  Opportunity,
  SentryEvent,
  JournalEntry,
  ChatResponse,
  Portfolio,
  SubWalletData,
  MonitorStatus,
  MCPInfo,
  ChatMessage,
  UserRules,
  ExecutionReceipt,
  TradeHistoryItem,
  SubWalletTrade,
  GuardianStatusData,
  BinanceMCPStatus,
  TodayPnLBreakdown,
} from "@/types";

import { AnimatedNumber } from "@/components/AnimatedNumber";

// Modular Components
import { Header } from "@/components/Header";
import { AgentCommandCenter } from "@/components/AgentCommandCenter";
import { PositionsManager } from "@/components/PositionsManager";
import { TradeHistoryView } from "@/components/TradeHistoryView";
import { MarketScanner } from "@/components/MarketScanner";
import { SentryRadarView } from "@/components/SentryRadarView";
import { DecisionJournalView } from "@/components/DecisionJournalView";
import { UserRulesModal } from "@/components/UserRulesModal";
import { NewTradeModal } from "@/components/NewTradeModal";
import { AdjustLevelsModal } from "@/components/AdjustLevelsModal";
import { EvaluateCoinModal } from "@/components/EvaluateCoinModal";
import { BinanceMcpModal } from "@/components/BinanceMcpModal";
import { InternalTransferModal } from "@/components/InternalTransferModal";
import { WalletsSummaryData } from "@/types";

type ActiveTab = "agent" | "positions" | "history" | "scanner" | "sentry" | "journal";

export default function SyraxApp() {
  // Navigation
  const [activeTab, setActiveTab] = useState<ActiveTab>("agent");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Core Data
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [subWalletData, setSubWalletData] = useState<SubWalletData | null>(null);
  const [tradeHistory, setTradeHistory] = useState<TradeHistoryItem[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [sentryEvents, setSentryEvents] = useState<SentryEvent[]>([]);
  const [journal, setJournal] = useState<JournalEntry[]>([]);
  const [monitorStatus, setMonitorStatus] = useState<MonitorStatus | null>(null);
  const [mcpInfo, setMcpInfo] = useState<MCPInfo | null>(null);
  const [binanceMcpStatus, setBinanceMcpStatus] = useState<BinanceMCPStatus | null>(null);
  const [guardianStatus, setGuardianStatus] = useState<GuardianStatusData | null>(null);
  const [todayPnL, setTodayPnL] = useState<TodayPnLBreakdown | null>(null);

  // User Rules / Mandate
  const [userRules, setUserRules] = useState<UserRules>({
    capital_usd: 500.0,
    max_risk_pct: 1.0,
    max_order_size_usd: 25.0,
    max_leverage: 10,
    require_stop_loss: true,
    sentry_exploit_filter: true,
    execution_mode: "AUTONOMOUS",
    target_allocations: { USDT: 40.0, BTC: 30.0, ETH: 15.0, SOL: 10.0, USDC: 5.0 },
  });

  // Copilot / Agent Command State
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResult, setChatResult] = useState<ChatResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      sender: "ai",
      text: "👋 SYRAX AI Trading Agent is online. Sub-Wallet and Sentry Exploit Radar initialized.",
      timestamp: "Just now",
    },
  ]);
  const [latestReceipt, setLatestExecutedOrder] = useState<ExecutionReceipt | null>(null);
  const chatAbortControllerRef = useRef<AbortController | null>(null);

  // Modals
  const [showRulesModal, setShowRulesModal] = useState(false);
  const [showNewTradeModal, setShowNewTradeModal] = useState(false);
  const [showBinanceMcpModal, setShowBinanceMcpModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferFromWallet, setTransferFromWallet] = useState('SPOT');
  const [transferToWallet, setTransferToWallet] = useState('USDT_FUTURES');
  const [walletsData, setWalletsData] = useState<WalletsSummaryData | null>(null);
  const [adjustTrade, setAdjustTrade] = useState<SubWalletTrade | null>(null);
  const [selectedCoin, setSelectedCoin] = useState<Opportunity | null>(null);
  const [adjustLoading, setAdjustLoading] = useState(false);
  const [newTradeLoading, setNewTradeLoading] = useState(false);

  // Filter States
  const [positionsFilter, setPositionsFilter] = useState<"ALL" | "FUTURES" | "SPOT" | "MARGIN">("ALL");
  const [historyFilter, setHistoryFilter] = useState<"ALL" | "SPOT" | "FUTURES" | "CONVERT" | "BUY" | "SELL">("ALL");
  const [historySearch, setHistorySearch] = useState("");
  const [scannerCategory, setScannerCategory] = useState<"ALL" | "FUTURES" | "ALPHA" | "SPOT">("ALL");
  const [scannerCategoryLoading, setScannerCategoryLoading] = useState(false);
  const [scannerVerdictFilter, setScannerVerdictFilter] = useState<"ALL" | "TRADEABLE" | "WATCH" | "TRAP">("ALL");
  const [scannerSearchQuery, setScannerSearchQuery] = useState("");
  const [scannerSearchLoading, setScannerSearchLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Live Binance Ticker Stream
  const [liveTickerMap, setLiveTickerMap] = useState<
    Record<string, { price: number; dir: "up" | "down" | null; change24h?: number; lastUpdate: number }>
  >({});
  const [tickerCount, setTickerCount] = useState<number>(0);
  const [isWsLive, setIsWsLive] = useState<boolean>(true);

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  // 1. Data Loader
  const loadData = async () => {
    setLoading(true);
    try {
      const [dash, scan, sub, sentry, jrnl, mon, mcp, rules, hist, mcpStat, guardStat, wallets] = await Promise.all([
        api.getDashboard(),
        api.getMarketScan(),
        api.getSubWallet(),
        api.getSentry(),
        api.getJournal(),
        api.getMonitorStatus(),
        api.getMCPInfo(),
        api.getUserRules(),
        api.getTradeHistory(),
        api.getBinanceMcpStatus(),
        api.getGuardianStatus(),
        api.getWalletsSummary(),
      ]);

      if (wallets) setWalletsData(wallets);

      if (dash?.portfolio) setPortfolio(dash.portfolio);
      if (dash?.today_pnl) setTodayPnL(dash.today_pnl);
      if (scan) setOpportunities(scan);
      if (sub) setSubWalletData(sub);
      if (sentry?.events) setSentryEvents(sentry.events);
      if (jrnl?.journal) setJournal(jrnl.journal);
      if (mon) setMonitorStatus(mon);
      if (mcp) setMcpInfo(mcp);
      if (rules?.rules) setUserRules(rules.rules);
      if (hist) setTradeHistory(hist);
      if (mcpStat) setBinanceMcpStatus(mcpStat);
      if (guardStat) setGuardianStatus(guardStat);
    } catch (err) {
      console.error("Failed to load telemetry:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // 5-second polling interval for live prices & sub-wallet
    const interval = setInterval(async () => {
      try {
        const [sub, mon, wallets] = await Promise.all([api.getSubWallet(), api.getMonitorStatus(), api.getWalletsSummary()]);
        if (sub) setSubWalletData(sub);
        if (mon) setMonitorStatus(mon);
        if (wallets) setWalletsData(wallets);
        setTickerCount((prev) => prev + 1);
      } catch {}
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // 2. Command Execution & Stop Handlers
  const handleStopExecution = () => {
    if (chatAbortControllerRef.current) {
      chatAbortControllerRef.current.abort();
      chatAbortControllerRef.current = null;
    }
    setChatLoading(false);
    const stopMsg: ChatMessage = {
      id: `stop-${Date.now()}`,
      sender: "ai",
      text: "🛑 AI Agent execution stopped by user. Ongoing cognitive analysis and order compilation was aborted safely. No trades were placed or funds modified.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setChatMessages((prev) => [...prev, stopMsg]);
    showToast("⏹️ AI execution stopped by user.");
  };

  const handleSendCommand = async (commandText: string) => {
    if (!commandText.trim() || chatLoading) return;
    const text = commandText.trim();

    // Abort any existing ongoing request
    if (chatAbortControllerRef.current) {
      chatAbortControllerRef.current.abort();
    }
    const controller = new AbortController();
    chatAbortControllerRef.current = controller;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await api.sendChatMessage(text, undefined, controller.signal);
      setChatResult(res);

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: "ai",
        text: res.headline || res.reason || "Mandate processed.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        response: res,
      };
      setChatMessages((prev) => [...prev, aiMsg]);

      if (res.active_rules) {
        setUserRules(res.active_rules);
      }

      if (res.execution_receipt) {
        setLatestExecutedOrder(res.execution_receipt);
        showToast(`⚡ ${res.execution_receipt.message || `Order Executed: ${res.execution_receipt.symbol || res.execution_receipt.action}`}`);
        const [sub, hist] = await Promise.all([api.getSubWallet(), api.getTradeHistory()]);
        if (sub) setSubWalletData(sub);
        if (hist) setTradeHistory(hist);
      } else {
        showToast(`Decision: ${res.decision}`);
      }

      const jrnl = await api.getJournal();
      if (jrnl?.journal) setJournal(jrnl.journal);
    } catch (err: any) {
      if (err?.name === "AbortError" || err?.message?.includes("aborted")) {
        console.log("Chat execution aborted by user.");
        return;
      }
      console.error(err);
      showToast("❌ Error executing command. Check backend.");
    } finally {
      chatAbortControllerRef.current = null;
      setChatLoading(false);
    }
  };

  const handleClearChat = () => {
    setChatMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: "ai",
        text: "👋 SYRAX AI Trading Agent conversation reset. How can I assist with your trading, market analysis, or sub-wallet positions today?",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setChatResult(null);
  };

  // 3. Trade Position Actions
  const handleCloseOngoingTrade = async (tradeId: string) => {
    setActionLoadingId(tradeId);
    try {
      const res = await api.closeSubWalletTrade(tradeId);
      if (res.success) {
        showToast(`Closed trade ${tradeId}. Proceeds credited to sub-wallet cash.`);
        if (res.trade) {
          setLatestExecutedOrder({
            action: "CLOSE",
            symbol: res.trade.symbol,
            market_type: res.trade.market_type,
            term: `CLOSE ${res.trade.side}`,
            order_id: res.trade.close_order_id || `ORD-CLS-${res.trade.symbol.slice(0, 3)}`,
            status: "CLOSED",
            entry_price: res.trade.exit_price || res.trade.entry_price,
            margin_usd: res.trade.margin_usd,
            fee_usd: res.trade.close_fee_usd,
            fee_breakdown: res.trade.close_fee_breakdown || (res.trade.close_fee_usd ? `$${res.trade.close_fee_usd.toFixed(4)} USDT` : undefined),
            realized_pnl_usd: res.trade.realized_pnl_usd,
            message: `Closed ${res.trade.symbol} position with ${Number(res.trade.realized_pnl_usd) >= 0 ? "+" : ""}$${Number(res.trade.realized_pnl_usd || 0).toFixed(2)} PnL`,
          });
        }
        const [sub, hist] = await Promise.all([api.getSubWallet(), api.getTradeHistory()]);
        if (sub) setSubWalletData(sub);
        if (hist) setTradeHistory(hist);
      } else {
        showToast(`Failed: ${res.error || "Could not close trade"}`);
      }
    } catch {
      showToast("Error closing trade");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSellHolding = async (asset: string) => {
    setActionLoadingId(`sell-${asset}`);
    try {
      const res = await api.sellSubWalletHolding(asset);
      if (res.success) {
        showToast(`⚡ Sold ${res.quantity_sold} ${asset} for $${res.notional_usd.toFixed(2)} USDT on Binance Spot`);
        if (res.trade) {
          setLatestExecutedOrder({
            action: "SELL",
            symbol: `${asset}USDT`,
            market_type: "SPOT",
            term: `SPOT SELL`,
            order_id: res.order_id,
            status: "FILLED",
            entry_price: res.price,
            margin_usd: res.notional_usd,
            notional_usd: res.notional_usd,
            fee_usd: res.fee_usd,
            fee_breakdown: res.fee_breakdown,
            return_capital: res.net_proceeds_usd,
            new_cash_usd: res.new_cash_usd,
            message: `Sold ${res.quantity_sold} ${asset} for $${res.notional_usd.toFixed(2)} USDT on Binance Spot`,
          });
        }
        const [sub, hist, dash] = await Promise.all([api.getSubWallet(), api.getTradeHistory(), api.getDashboard()]);
        if (sub) setSubWalletData(sub);
        if (hist) setTradeHistory(hist);
        if (dash?.portfolio) setPortfolio(dash.portfolio);
      } else {
        showToast(`Failed: ${res.error || "Could not sell asset"}`);
      }
    } catch {
      showToast("Error selling asset");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleOpenNewTrade = async (trade: {
    symbol: string;
    side: "BUY" | "SELL";
    amount: number;
    marketType: "SPOT" | "FUTURES" | "MARGIN";
    leverage: number;
    marginType: "ISOLATED" | "CROSS";
    stopLoss?: number;
    takeProfit?: number;
  }) => {
    setNewTradeLoading(true);
    try {
      const res = await api.openSubWalletOrder(
        trade.symbol,
        trade.side,
        trade.amount,
        trade.stopLoss,
        trade.takeProfit,
        trade.marketType,
        trade.leverage,
        trade.marginType
      );
      if (res.success) {
        showToast(`Position opened in Sub-Wallet: ${trade.side} $${trade.amount} ${trade.symbol}`);
        setShowNewTradeModal(false);
        if (res.trade) {
          setLatestExecutedOrder({
            action: res.trade.side,
            symbol: res.trade.symbol,
            market_type: res.trade.market_type,
            term: res.trade.term || `${res.trade.side} ${res.trade.leverage}x`,
            order_id: res.trade.order_id,
            status: "FILLED",
            entry_price: res.trade.entry_price,
            margin_usd: res.trade.margin_usd,
            notional_usd: res.trade.notional_usd,
            leverage: res.trade.leverage,
            fee_usd: res.trade.fee_usd,
            fee_breakdown: res.trade.fee_breakdown,
            stop_loss: res.trade.stop_loss,
            take_profit: res.trade.take_profit,
            message: `Order ${res.trade.order_id} filled in Sub-Wallet`,
          });
        }
        const [sub, hist] = await Promise.all([api.getSubWallet(), api.getTradeHistory()]);
        if (sub) setSubWalletData(sub);
        if (hist) setTradeHistory(hist);
      } else {
        showToast(`Order failed: ${res.error || "Execution rejected"}`);
      }
    } catch {
      showToast("Error executing order");
    } finally {
      setNewTradeLoading(false);
    }
  };

  const handleSaveTradeLevels = async (sl?: number, tp?: number) => {
    if (!adjustTrade) return;
    setAdjustLoading(true);
    try {
      const res = await api.updateSubWalletTradeLevels(adjustTrade.trade_id, sl, tp);
      if (res.success) {
        showToast(`Levels updated for ${adjustTrade.symbol}: SL $${sl ?? "None"}, TP $${tp ?? "None"}`);
        setAdjustTrade(null);
        const sub = await api.getSubWallet();
        if (sub) setSubWalletData(sub);
      } else {
        showToast(`Failed: ${res.error || "Unknown error"}`);
      }
    } catch {
      showToast("Error updating trade levels");
    } finally {
      setAdjustLoading(false);
    }
  };

  const handleDirectSubWalletOrder = async (coin: Opportunity) => {
    setLoading(true);
    try {
      const notional = Math.min(userRules.max_order_size_usd, userRules.capital_usd);
      const res = await api.openSubWalletOrder(
        coin.symbol,
        "BUY",
        notional,
        coin.setup?.stop_loss,
        coin.setup?.take_profit
      );
      if (res.success) {
        showToast(`⚡ Order placed in Sub-Wallet: BUY $${notional} ${coin.symbol}`);
        setSelectedCoin(null);
        if (res.trade) {
          setLatestExecutedOrder({
            action: res.trade.side,
            symbol: res.trade.symbol,
            market_type: res.trade.market_type,
            term: res.trade.term || "SPOT BUY",
            order_id: res.trade.order_id,
            status: "FILLED",
            entry_price: res.trade.entry_price,
            margin_usd: res.trade.margin_usd,
            notional_usd: res.trade.notional_usd,
            leverage: res.trade.leverage,
            fee_usd: res.trade.fee_usd,
            fee_breakdown: res.trade.fee_breakdown,
            stop_loss: res.trade.stop_loss,
            take_profit: res.trade.take_profit,
            message: `Order ${res.trade.order_id} filled in Sub-Wallet`,
          });
        }
        const [sub, hist] = await Promise.all([api.getSubWallet(), api.getTradeHistory()]);
        if (sub) setSubWalletData(sub);
        if (hist) setTradeHistory(hist);
        setActiveTab("positions");
      } else {
        showToast(`Order rejected: ${res.error || "Risk check failed"}`);
      }
    } catch {
      showToast("Error executing order");
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerProtect = async (token: string = "SOL") => {
    setLoading(true);
    try {
      const res = await api.triggerEmergencyProtect(token);
      showToast(`Protective action executed: ${token} hedged to USDT`);
      await loadData();
    } catch {
      showToast("Error triggering protect");
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateExploit = async () => {
    setLoading(true);
    try {
      await api.simulateSentryEvent("SOL");
      showToast("Simulated threat injected into Sentry radar!");
      await loadData();
    } catch {
      showToast("Error simulating threat");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleMonitor = async () => {
    try {
      const updated = await api.toggleMonitor();
      if (updated) {
        setMonitorStatus(updated);
        showToast(updated.is_paused ? "24/7 Sentinel PAUSED" : "24/7 Sentinel RESUMED");
      }
    } catch {
      showToast("Error toggling monitor");
    }
  };

  const handleCopyMcpUrl = () => {
    navigator.clipboard.writeText(mcpInfo?.mcp_url || "http://127.0.0.1:8001/mcp/sse");
    showToast("Copied MCP SSE URL to clipboard!");
  };

  const handleSaveUserRules = async (updated: Partial<UserRules>) => {
    try {
      const res = await api.updateUserRules(updated);
      if (res?.rules) {
        setUserRules(res.rules);
        showToast("✅ Trading mandate rules updated successfully!");
      }
    } catch {
      showToast("Failed to update rules");
    }
  };

  const handleScannerCategoryChange = async (cat: "ALL" | "FUTURES" | "ALPHA" | "SPOT") => {
    setScannerCategory(cat);
    setScannerCategoryLoading(true);
    try {
      const scan = await api.getMarketScan(cat);
      setOpportunities(scan);
    } catch (err) {
      console.error(err);
    } finally {
      setScannerCategoryLoading(false);
    }
  };

  const handleScannerSearch = async (query: string) => {
    if (!query.trim()) return;
    setScannerSearchLoading(true);
    try {
      const data = await api.getSymbolAnalysis(query.trim().toUpperCase());
      const coin = (data?.analysis || data) as Opportunity;
      if (coin && coin.symbol) {
        setSelectedCoin(coin);
        setOpportunities((prev) => [coin, ...prev.filter((c) => c.symbol !== coin.symbol)]);
        showToast(`Fetched live Binance data for ${coin.symbol}`);
      }
    } catch {
      showToast(`Could not find ${query} on Binance`);
    } finally {
      setScannerSearchLoading(false);
    }
  };

  const handleCancelPendingOrder = async (orderId: string) => {
    setActionLoadingId(`cancel-${orderId}`);
    try {
      const res = await api.cancelPendingOrder(orderId);
      if (res.success) {
        showToast(`Order ${orderId} canceled. Unfilled margin returned to cash.`);
        await loadData();
      } else {
        showToast(`Failed to cancel: ${res.error || 'Unknown error'}`);
      }
    } catch {
      showToast("Network error canceling order");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSimulateFill = async (orderId: string, fillPct: number) => {
    setActionLoadingId(`fill-${orderId}`);
    try {
      const res = await api.simulateFillOrder(orderId, fillPct);
      if (res.success) {
        showToast(`Simulated fill event: ${fillPct}% lot executed on Binance orderbook.`);
        await loadData();
      } else {
        showToast(`Fill simulation failed: ${res.error || 'Unknown error'}`);
      }
    } catch {
      showToast("Network error simulating fill");
    } finally {
      setActionLoadingId(null);
    }
  };

  const availableCash = subWalletData?.analysis?.available_cash_usd ?? portfolio?.available_cash_usd ?? 250.0;
  const totalValue = subWalletData?.analysis?.total_portfolio_value_usd ?? portfolio?.total_value_usd ?? 500.0;
  const ongoingCount = subWalletData?.ongoing_trades?.length ?? 0;

  return (
    <div className="min-h-screen bg-[#070B13] text-slate-100 flex flex-col antialiased">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed top-5 right-5 z-50 bg-indigo-950/95 border border-indigo-500/50 text-indigo-200 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 backdrop-blur-md animate-in fade-in slide-in-from-top-3">
          <Info className="w-5 h-5 text-indigo-400 shrink-0" />
          <span className="text-xs font-semibold">{notification}</span>
        </div>
      )}

      {/* 1. TOP HEADER */}
      <Header
        loading={loading}
        onRefresh={loadData}
        monitorStatus={monitorStatus}
        onToggleMonitor={handleToggleMonitor}
        mcpInfo={mcpInfo}
        onCopyMcpUrl={handleCopyMcpUrl}
        isWsLive={isWsLive}
        tickerCount={tickerCount}
        portfolio={portfolio}
        subWalletData={subWalletData}
        guardianStatus={guardianStatus}
        binanceMcpStatus={binanceMcpStatus}
        onOpenRules={() => setShowRulesModal(true)}
        onOpenBinanceMcp={() => setShowBinanceMcpModal(true)}
        activeMandateRiskPct={userRules.max_risk_pct}
        onOpenTransfer={() => {
          setTransferFromWallet('SPOT');
          setTransferToWallet('USDT_FUTURES');
          setShowTransferModal(true);
        }}
      />

      {/* 2. AGENT-CENTRIC MAIN NAVIGATION */}
      <nav className="border-b border-slate-800/80 bg-[#090E1A] sticky top-16 sm:top-[68px] z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 sm:space-x-3 text-xs overflow-x-auto">
          {[
            { id: "agent", label: "Agent Command Center", icon: Terminal, primary: true },
            { id: "positions", label: "Positions & Sub-Wallet", icon: Activity, badge: ongoingCount },
            { id: "history", label: "Trade History & Receipts", icon: Clock, badge: tradeHistory.length },
            { id: "scanner", label: "Market Discovery", icon: TrendingUp },
            { id: "sentry", label: "Sentry Radar", icon: AlertTriangle, hasAlert: sentryEvents.some((e) => e.severity === "CRITICAL" || e.severity === "HIGH") },
            { id: "journal", label: "Cognitive Journal", icon: BookOpen },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ActiveTab)}
                className={`flex items-center gap-2 py-3 px-3.5 border-b-2 font-bold whitespace-nowrap transition-all ${
                  isActive
                    ? tab.primary
                      ? "border-indigo-500 text-white bg-indigo-500/10 shadow-sm"
                      : "border-indigo-500 text-white bg-slate-800/40"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                <span>{tab.label}</span>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {tab.badge}
                  </span>
                )}
                {tab.hasAlert && (
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* 3. MAIN CONTENT BODY */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24 space-y-6">
        {/* VIEW 1: AGENT COMMAND CENTER (Clean, Focused, Conversational) */}
        {activeTab === "agent" && (
          <div className="animate-in fade-in duration-150">
            <AgentCommandCenter
              chatInput={chatInput}
              setChatInput={setChatInput}
              onSendCommand={handleSendCommand}
              onStopExecution={handleStopExecution}
              chatLoading={chatLoading}
              chatResult={chatResult}
              chatMessages={chatMessages}
              userRules={userRules}
              onOpenRules={() => setShowRulesModal(true)}
              latestReceipt={latestReceipt}
              availableCashUsd={availableCash}
              onClearHistory={handleClearChat}
            />
          </div>
        )}

        {/* VIEW 2: POSITIONS & SUB-WALLET (Unified Portfolio & Sub-Account Dashboard) */}
        {activeTab === "positions" && (
          <div className="animate-in fade-in duration-150">
            <PositionsManager
              subWalletData={subWalletData}
              liveTickerMap={liveTickerMap}
              filter={positionsFilter}
              setFilter={setPositionsFilter}
              onOpenNewTrade={() => setShowNewTradeModal(true)}
              onCloseTrade={handleCloseOngoingTrade}
              onOpenAdjust={(trade) => setAdjustTrade(trade)}
              onRefresh={loadData}
              actionLoadingId={actionLoadingId}
              onSellHolding={handleSellHolding}
              onCancelOrder={handleCancelPendingOrder}
              onSimulateFill={handleSimulateFill}
              binanceMcpStatus={binanceMcpStatus}
              todayPnL={todayPnL}
              userRules={userRules}
              onOpenBinanceMcp={() => setShowBinanceMcpModal(true)}
              walletsData={walletsData}
              onOpenTransfer={(from, to) => {
                if (from) setTransferFromWallet(from);
                if (to) setTransferToWallet(to);
                setShowTransferModal(true);
              }}
            />
          </div>
        )}

        {/* VIEW 3: TRADE HISTORY */}
        {activeTab === "history" && (
          <div className="animate-in fade-in duration-150">
            <TradeHistoryView
              tradeHistory={tradeHistory}
              filter={historyFilter}
              setFilter={setHistoryFilter}
              searchQuery={historySearch}
              setSearchQuery={setHistorySearch}
              onRefresh={loadData}
            />
          </div>
        )}

        {/* VIEW 4: MARKET SCANNER */}
        {activeTab === "scanner" && (
          <div className="animate-in fade-in duration-150">
            <MarketScanner
              opportunities={opportunities}
              category={scannerCategory}
              onCategoryChange={handleScannerCategoryChange}
              categoryLoading={scannerCategoryLoading}
              verdictFilter={scannerVerdictFilter}
              setVerdictFilter={setScannerVerdictFilter}
              searchQuery={scannerSearchQuery}
              setSearchQuery={setScannerSearchQuery}
              onSearch={handleScannerSearch}
              searchLoading={scannerSearchLoading}
              onSelectCoin={(coin) => setSelectedCoin(coin)}
              liveTickerMap={liveTickerMap}
            />
          </div>
        )}

        {/* VIEW 5: SENTRY RADAR */}
        {activeTab === "sentry" && (
          <div className="animate-in fade-in duration-150">
            <SentryRadarView
              events={sentryEvents}
              onTriggerProtect={handleTriggerProtect}
              onSimulateThreat={handleSimulateExploit}
              loading={loading}
            />
          </div>
        )}

        {/* VIEW 6: COGNITIVE JOURNAL */}
        {activeTab === "journal" && (
          <div className="animate-in fade-in duration-150">
            <DecisionJournalView journal={journal} />
          </div>
        )}
      </main>

      {/* 4. MODALS */}
      <UserRulesModal
        isOpen={showRulesModal}
        onClose={() => setShowRulesModal(false)}
        userRules={userRules}
        onSaveRules={handleSaveUserRules}
      />

      <NewTradeModal
        isOpen={showNewTradeModal}
        onClose={() => setShowNewTradeModal(false)}
        onSubmit={handleOpenNewTrade}
        loading={newTradeLoading}
      />

      <AdjustLevelsModal
        trade={adjustTrade}
        onClose={() => setAdjustTrade(null)}
        onSave={handleSaveTradeLevels}
        loading={adjustLoading}
      />

      <EvaluateCoinModal
        coin={selectedCoin}
        onClose={() => setSelectedCoin(null)}
        onExecuteTrade={handleDirectSubWalletOrder}
        loading={loading}
      />

      <InternalTransferModal
        isOpen={showTransferModal}
        onClose={() => setShowTransferModal(false)}
        walletsData={walletsData}
        onRefresh={loadData}
        initialFromWallet={transferFromWallet}
        initialToWallet={transferToWallet}
      />

      <BinanceMcpModal
        isOpen={showBinanceMcpModal}
        onClose={() => setShowBinanceMcpModal(false)}
        mcpStatus={binanceMcpStatus}
        onRefreshStatus={loadData}
      />
    </div>
  );
}
