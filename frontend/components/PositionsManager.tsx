import { MultiWalletBreakdownCard } from "./MultiWalletBreakdownCard";
import { WalletsSummaryData } from "@/types";
import React from "react";
import { Activity, Plus, RefreshCw, Sliders, Trash2, ArrowUpRight, ArrowDownRight, Layers, Shield, PieChart, Coins, Wallet, Clock, CheckCircle, XCircle, Zap, TrendingUp, DollarSign, Server } from "lucide-react";
import { SubWalletTrade, SubWalletData, PendingOrder, BinanceMCPStatus, TodayPnLBreakdown, UserRules } from "@/types";
import { AnimatedNumber } from "./AnimatedNumber";

interface PositionsManagerProps {
  subWalletData: SubWalletData | null;
  liveTickerMap: Record<string, { price: number; dir: "up" | "down" | null; change24h?: number; lastUpdate: number }>;
  filter: "ALL" | "FUTURES" | "SPOT" | "MARGIN";
  setFilter: (f: "ALL" | "FUTURES" | "SPOT" | "MARGIN") => void;
  onOpenNewTrade: () => void;
  onCloseTrade: (tradeId: string) => void;
  onOpenAdjust: (trade: SubWalletTrade) => void;
  onRefresh: () => void;
  actionLoadingId: string | null;
  onSellHolding?: (asset: string) => void;
  onCancelOrder?: (orderId: string) => void;
  onSimulateFill?: (orderId: string, fillPct: number) => void;
  binanceMcpStatus?: BinanceMCPStatus | null;
  todayPnL?: TodayPnLBreakdown | null;
  userRules?: UserRules;
  onOpenBinanceMcp?: () => void;
  walletsData?: WalletsSummaryData | null;
  onOpenTransfer?: (from?: string, to?: string) => void;
}

export const PositionsManager: React.FC<PositionsManagerProps> = ({
  subWalletData,
  liveTickerMap,
  filter,
  setFilter,
  onOpenNewTrade,
  onCloseTrade,
  onOpenAdjust,
  onRefresh,
  actionLoadingId,
  onSellHolding,
  onCancelOrder,
  onSimulateFill,
  binanceMcpStatus,
  todayPnL,
  userRules,
  onOpenBinanceMcp,
  walletsData,
  onOpenTransfer,
}) => {
  const ongoingTrades = subWalletData?.ongoing_trades || [];
  const holdings = subWalletData?.analysis?.holdings || [];
  const pendingOrders = subWalletData?.pending_orders || subWalletData?.analysis?.pending_orders || [];
  const totalValue = subWalletData?.analysis?.total_portfolio_value_usd || 0;
  const liquidCash = subWalletData?.analysis?.available_cash_usd || 0;
  const reservedCash = subWalletData?.analysis?.reserved_cash_usd || 0;

  const colorPalette = [
    "bg-indigo-500 text-indigo-300 border-indigo-500/30",
    "bg-amber-500 text-amber-300 border-amber-500/30",
    "bg-purple-500 text-purple-300 border-purple-500/30",
    "bg-cyan-500 text-cyan-300 border-cyan-500/30",
    "bg-emerald-500 text-emerald-300 border-emerald-500/30",
    "bg-pink-500 text-pink-300 border-pink-500/30",
  ];

  const barColorPalette = [
    "bg-indigo-500",
    "bg-amber-500",
    "bg-purple-500",
    "bg-cyan-500",
    "bg-emerald-500",
    "bg-pink-500",
  ];

  const filteredTrades = ongoingTrades.filter((t) => {
    if (filter === "ALL") return true;
    if (filter === "FUTURES") return t.market_type === "FUTURES";
    if (filter === "SPOT") return t.market_type === "SPOT";
    if (filter === "MARGIN") return t.market_type === "MARGIN";
    return true;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* 1. Binance Agent OS MCP Account Connectivity Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[#0B1224] via-[#0E172E] to-[#0A1020] border border-amber-500/30 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0 shadow-inner">
            <span className="text-xl font-mono">🔶</span>
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-white tracking-wide">
                Binance Agent OS — Sub-Account &amp; Portfolio Dashboard
              </h3>
              <span
                className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                  binanceMcpStatus?.connected
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                }`}
              >
                {binanceMcpStatus?.connected ? "● MCP CONNECTED" : "○ SIMULATED / DEMO MODE"}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700">
                ENV: {binanceMcpStatus?.account_scope?.environment || "BINANCE AGENT OS"}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {binanceMcpStatus?.connected
                ? `Connected to Agentic Sub-Account [${binanceMcpStatus.account_scope?.sub_account_id}]. MCP is the live source of truth.`
                : "Connect your official Binance Agentic Sub-Account via MCP (https://agent.binance.com/mcp/agentic) for real live portfolio synchronization."}
            </p>
          </div>
        </div>

        {onOpenBinanceMcp && (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onOpenBinanceMcp}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2 ${
                binanceMcpStatus?.connected
                  ? "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                  : "bg-amber-500 hover:bg-amber-400 text-black shadow-amber-500/20 active:scale-95"
              }`}
            >
              <span className="font-mono">🔶</span>
              <span>{binanceMcpStatus?.connected ? "Manage Binance MCP" : "Connect Binance MCP"}</span>
            </button>
          </div>
        )}
      </div>

      {/* 2. Today's P&L & Live Telemetry Grid */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <span>Live Account Telemetry &amp; Today&apos;s P&amp;L Analysis</span>
            <span className="text-[10px] font-mono text-indigo-400 lowercase font-normal">
              (UTC 00:00:00 - Now)
            </span>
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            Binance Day Cycle Standard
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
          {/* 1. TODAY'S P&L (PROMINENT FIRST CARD) */}
          <div className="p-4 rounded-xl bg-gradient-to-b from-[#0F172A] to-[#0B101D] border border-indigo-500/30 space-y-1.5 shadow-lg relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-[11px]">
              <span className="font-semibold text-indigo-300">Today&apos;s Total P&amp;L</span>
              <TrendingUp
                className={`w-3.5 h-3.5 ${
                  (todayPnL?.total_pnl_usd ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              />
            </div>
            <div className="flex items-baseline gap-2">
              <div
                className={`text-xl font-bold font-mono ${
                  (todayPnL?.total_pnl_usd ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {(todayPnL?.total_pnl_usd ?? 0) >= 0 ? "+" : ""}
                <AnimatedNumber value={todayPnL?.total_pnl_usd ?? 0} prefix="$" />
              </div>
              <span
                className={`text-[11px] font-mono font-bold ${
                  (todayPnL?.pnl_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                ({(todayPnL?.pnl_pct ?? 0) >= 0 ? "+" : ""}
                {(todayPnL?.pnl_pct ?? 0).toFixed(2)}%)
              </span>
            </div>
            <div className="pt-1.5 border-t border-slate-800/80 grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-400">
              <div>
                <span>Realized: </span>
                <span className={(todayPnL?.realized_pnl_usd ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                  {(todayPnL?.realized_pnl_usd ?? 0) >= 0 ? "+" : ""}${(todayPnL?.realized_pnl_usd ?? 0).toFixed(2)}
                </span>
              </div>
              <div>
                <span>Unrealized: </span>
                <span className={(todayPnL?.unrealized_pnl_usd ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                  {(todayPnL?.unrealized_pnl_usd ?? 0) >= 0 ? "+" : ""}${(todayPnL?.unrealized_pnl_usd ?? 0).toFixed(2)}
                </span>
              </div>
              <div className="col-span-2 text-slate-500">
                Fees: -${(todayPnL?.fees_usd ?? 0).toFixed(4)} USDT
              </div>
            </div>
          </div>

          {/* 2. Total Sub-Wallet Value */}
          <div className="p-4 rounded-xl bg-[#0B101D] border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[11px]">
              <span>Sub-Account Net Value</span>
              <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl font-bold font-mono text-white">
              <AnimatedNumber value={totalValue} prefix="$" />
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              {binanceMcpStatus?.connected ? "Live MCP Balance" : "Simulated Margin Base"}
            </div>
          </div>

          {/* 3. Liquid Cash */}
          <div className="p-4 rounded-xl bg-[#0B101D] border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[11px]">
              <span>Available Cash (USDT)</span>
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-xl font-bold font-mono text-white">
              <AnimatedNumber value={liquidCash} prefix="$" />
            </div>
            <div className="text-[11px] text-slate-400">
              {((liquidCash / (totalValue || 1)) * 100).toFixed(1)}% Free Reserves
            </div>
          </div>

          {/* 4. Deterministic 1% Risk Cap */}
          <div className="p-4 rounded-xl bg-[#0B101D] border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[11px]">
              <span>Max Allowable Loss</span>
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xl font-bold font-mono text-white">
              <AnimatedNumber value={((userRules?.capital_usd ?? 500) * (userRules?.max_risk_pct ?? 1.0)) / 100} prefix="$" />
            </div>
            <div className="text-[11px] text-indigo-400 font-medium">
              Strict {userRules?.max_risk_pct ?? 1.0}% Mandate
            </div>
          </div>

          {/* 5. Ongoing Positions */}
          <div className="p-4 rounded-xl bg-[#0B101D] border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[11px]">
              <span>Ongoing Active Trades</span>
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl font-bold font-mono text-white">{ongoingTrades.length} Positions</div>
            <div className="text-[11px] text-slate-400 flex items-center justify-between">
              <span>24/7 Guard:</span>
              <span className="text-emerald-400 font-semibold font-mono">ACTIVE</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Binance Multi-Wallet Breakdown & Internal Transfer Engine */}
      <MultiWalletBreakdownCard
        walletsData={walletsData || null}
        onOpenTransfer={onOpenTransfer || (() => {})}
        onRefresh={onRefresh}
      />

      {/* 4. Asset Allocation & Sub-Wallet Holdings Breakdown */}
      {holdings.length > 0 && (
        <div className="p-5 rounded-2xl bg-[#0A0F1D] border border-slate-800/90 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <PieChart className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Sub-Wallet Asset Allocation & Token Balances</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {holdings.length} Assets Held
                  </span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Real-time token holdings, free balances, and reserved limit order allocations.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 text-[10px] block uppercase">Total Balance</span>
                <span className="font-bold text-white">${totalValue.toFixed(2)}</span>
              </div>
              <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 text-[10px] block uppercase">Free Liquid Cash</span>
                <span className="font-bold text-emerald-400">${liquidCash.toFixed(2)}</span>
              </div>
              {reservedCash > 0 && (
                <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-cyan-500/30">
                  <span className="text-cyan-400 text-[10px] block uppercase">Reserved Margin</span>
                  <span className="font-bold text-cyan-300">${reservedCash.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Allocation Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Current Allocation Breakdown</span>
              <span className="font-mono text-slate-300">100% Total Delegated</span>
            </div>
            <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden flex p-0.5 border border-slate-800 gap-0.5">
              {holdings.map((h, idx) => (
                <div
                  key={h.asset}
                  style={{ width: `${Math.max(h.actual_allocation_pct, 2)}%` }}
                  className={`h-full rounded-sm transition-all duration-500 ${barColorPalette[idx % barColorPalette.length]}`}
                  title={`${h.asset}: ${h.actual_allocation_pct.toFixed(1)}% ($${h.value_usd.toFixed(2)})`}
                />
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-1">
              {holdings.map((h, idx) => (
                <div key={h.asset} className="flex items-center gap-1.5 text-[11px]">
                  <span className={`w-2 h-2 rounded-full ${barColorPalette[idx % barColorPalette.length]}`} />
                  <span className="font-bold text-white">{h.asset}</span>
                  <span className="text-slate-400 font-mono">{h.actual_allocation_pct.toFixed(1)}%</span>
                  <span className="text-slate-500 text-[10px]">(${h.value_usd.toFixed(2)})</span>
                </div>
              ))}
            </div>
          </div>

          {/* Holdings Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-1">
            {holdings.map((h, idx) => {
              const badgeClass = colorPalette[idx % colorPalette.length];
              const freeQty = h.free_quantity !== undefined ? h.free_quantity : h.quantity;
              const lockedQty = h.locked_quantity || 0;

              return (
                <div
                  key={h.asset}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-all flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between gap-1 mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className={`px-2 py-0.5 rounded-md text-xs font-mono font-black border ${badgeClass}`}>
                        {h.asset}
                      </span>
                    </div>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                        h.drift_status === "BALANCED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : h.drift_status === "OVERWEIGHT"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                      }`}
                    >
                      {h.drift_status}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="text-[10px] text-slate-400">Free Balance</div>
                    <div className="text-sm font-mono font-bold text-white">
                      {freeQty < 0.01 && freeQty > 0
                        ? freeQty.toFixed(6)
                        : freeQty.toLocaleString(undefined, { maximumFractionDigits: 4 })}{" "}
                      <span className="text-xs text-slate-400 font-normal">{h.asset}</span>
                    </div>

                    {lockedQty > 0 && (
                      <div className="text-[10px] font-mono text-cyan-400 flex items-center justify-between">
                        <span>Locked in Limit:</span>
                        <span>{lockedQty.toFixed(4)} {h.asset}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/40">
                      <span className="text-slate-400">USD Value:</span>
                      <span className="font-mono font-bold text-emerald-400">${h.value_usd.toFixed(2)}</span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span>Price: ${h.price_usd > 100 ? h.price_usd.toLocaleString(undefined, { maximumFractionDigits: 2 }) : h.price_usd.toFixed(4)}</span>
                      <span>Target: {h.target_allocation_pct.toFixed(0)}%</span>
                    </div>

                    {h.asset !== "USDT" && onSellHolding && (
                      <button
                        onClick={() => onSellHolding(h.asset)}
                        disabled={actionLoadingId === `sell-${h.asset}` || freeQty <= 0}
                        className="mt-2.5 w-full py-1.5 px-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-bold transition-all flex items-center justify-center gap-1.5 active:scale-95 disabled:opacity-50"
                      >
                        <Coins className="w-3 h-3 text-rose-400" />
                        <span>{actionLoadingId === `sell-${h.asset}` ? "Selling..." : `Sell Free ${h.asset}`}</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Pending Limit Orders Section */}
      {pendingOrders.length > 0 && (
        <div className="p-5 rounded-2xl bg-[#0A0F1D] border border-cyan-500/30 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <Clock className="w-4 h-4 animate-spin text-cyan-400" style={{ animationDuration: '6s' }} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Pending Limit Orders (Awaiting Fill)</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    {pendingOrders.length} Pending
                  </span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Orders residing on Binance orderbook with capital securely locked in reserve.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono px-2 py-1 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                BINANCE AGENTIC SUB-ACCOUNT
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-medium">
                <tr>
                  <th className="p-3">Order ID / Pair</th>
                  <th className="p-3">Side / Type</th>
                  <th className="p-3">Limit Price</th>
                  <th className="p-3">Live Distance</th>
                  <th className="p-3">Fill Progress</th>
                  <th className="p-3">Reserved Margin</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {pendingOrders.map((ord) => {
                  const base = ord.symbol.replace("USDT", "");
                  const isBuy = ord.side === "BUY";
                  const pct = ord.fill_percentage || 0;
                  const dist = ord.distance_to_market_pct || 0;

                  return (
                    <tr key={ord.order_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3">
                        <div className="font-mono font-bold text-white">{ord.symbol}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{ord.order_id}</div>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                          isBuy ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        }`}>
                          {ord.term || `LIMIT ${ord.side}`}
                        </span>
                        <div className="text-[10px] text-slate-400 mt-0.5 font-mono">{ord.market_type}</div>
                      </td>
                      <td className="p-3">
                        <div className="font-mono font-bold text-cyan-300">
                          ${ord.limit_price < 0.01 ? ord.limit_price.toFixed(6) : ord.limit_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                        </div>
                        {ord.average_fill_price && (
                          <div className="text-[10px] text-slate-400">Avg: ${ord.average_fill_price.toLocaleString()}</div>
                        )}
                      </td>
                      <td className="p-3">
                        <span className={`font-mono text-xs font-bold ${dist <= 0 ? "text-cyan-400" : "text-amber-400"}`}>
                          {dist > 0 ? `+${dist.toFixed(1)}%` : `${dist.toFixed(1)}%`}
                        </span>
                        <div className="text-[10px] text-slate-500">to market</div>
                      </td>
                      <td className="p-3 min-w-[140px]">
                        <div className="flex items-center justify-between text-[10px] text-slate-300 font-mono mb-1">
                          <span>{pct.toFixed(1)}% Filled</span>
                          <span>{ord.filled_quantity.toFixed(4)} / {ord.requested_quantity.toFixed(4)} {base}</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                          <div
                            style={{ width: `${Math.min(100, Math.max(pct, 0))}%` }}
                            className="h-full bg-cyan-400 rounded-full transition-all duration-300"
                          />
                        </div>
                      </td>
                      <td className="p-3 font-mono">
                        <div className="font-bold text-white">${ord.reserved_usd.toFixed(2)} USDT</div>
                        <div className="text-[10px] text-slate-500">{ord.status}</div>
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {onSimulateFill && (
                            <button
                              onClick={() => onSimulateFill(ord.order_id, 40)}
                              disabled={actionLoadingId === `fill-${ord.order_id}`}
                              className="px-2 py-1 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] font-bold transition-all flex items-center gap-1 active:scale-95"
                              title="Simulate 40% Partial Fill"
                            >
                              <Zap className="w-2.5 h-2.5" />
                              <span>Fill +40%</span>
                            </button>
                          )}
                          {onCancelOrder && (
                            <button
                              onClick={() => onCancelOrder(ord.order_id)}
                              disabled={actionLoadingId === `cancel-${ord.order_id}`}
                              className="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] font-bold transition-all flex items-center gap-1 active:scale-95"
                            >
                              <XCircle className="w-2.5 h-2.5" />
                              <span>{actionLoadingId === `cancel-${ord.order_id}` ? "Canceling..." : "Cancel"}</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Ongoing Trades & Live Positions</span>
            </h3>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
              {ongoingTrades.length} Active
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Mark-to-market live valuation against Binance Spot & USDⓈ-M Perps orderbook.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
            <span>Sync Prices</span>
          </button>
          <button
            onClick={onOpenNewTrade}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Position</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900/90 border border-slate-800/80 w-fit text-xs">
        {(["ALL", "SPOT", "FUTURES", "MARGIN"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              filter === f
                ? "bg-slate-700 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Positions Table */}
      {filteredTrades.length === 0 ? (
        <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
          <Layers className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">No active positions open in this category</p>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Give SYRAX a command or open a position manually to deploy capital under your 1.0% risk mandate.
          </p>
          <button
            onClick={onOpenNewTrade}
            className="mt-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            Open Sub-Wallet Position
          </button>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-[#0A0F1D] overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-medium">
                <tr>
                  <th className="p-3.5">Instrument / Type</th>
                  <th className="p-3.5">Side & Leverage</th>
                  <th className="p-3.5">Entry Price</th>
                  <th className="p-3.5">Live Mark Price</th>
                  <th className="p-3.5">Margin / Size</th>
                  <th className="p-3.5">Unrealized PnL</th>
                  <th className="p-3.5">SL / TP Gates</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTrades.map((trade) => {
                  const ticker = liveTickerMap[trade.symbol];
                  const livePrice = ticker?.price ?? trade.current_price ?? trade.entry_price;
                  const isBuy = trade.side === "BUY";
                  const isFutures = trade.market_type === "FUTURES";

                  let pnlUsd = 0;
                  if (livePrice > 0 && trade.entry_price > 0 && trade.quantity > 0) {
                    pnlUsd = isBuy
                      ? (livePrice - trade.entry_price) * trade.quantity
                      : (trade.entry_price - livePrice) * trade.quantity;
                  } else {
                    pnlUsd = trade.unrealized_pnl_usd ?? 0;
                  }

                  const pnlPct = trade.margin_usd && trade.margin_usd > 0
                    ? (pnlUsd / trade.margin_usd) * 100
                    : trade.notional_usd > 0
                    ? (pnlUsd / trade.notional_usd) * 100
                    : 0;

                  return (
                    <tr key={trade.trade_id} className="hover:bg-slate-800/30 transition-colors">
                      {/* Instrument */}
                      <td className="p-3.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white font-mono">{trade.symbol}</span>
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold uppercase ${
                              trade.market_type === "FUTURES"
                                ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                                : trade.market_type === "MARGIN"
                                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                                : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                            }`}
                          >
                            {trade.market_type}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">{trade.trade_id}</div>
                      </td>

                      {/* Side & Leverage */}
                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono flex items-center gap-1 ${
                              isBuy
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            {isBuy ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                            {trade.side}
                          </span>
                          {isFutures && trade.leverage && (
                            <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                              {trade.leverage}x
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {trade.margin_type || "ISOLATED"}
                        </div>
                      </td>

                      {/* Entry Price */}
                      <td className="p-3.5 font-mono">
                        <div className="font-bold text-white">
                          ${trade.entry_price < 0.01 ? trade.entry_price.toFixed(6) : trade.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {trade.quantity} {trade.symbol.replace("USDT", "")}
                        </div>
                      </td>

                      {/* Live Mark Price */}
                      <td className="p-3.5 font-mono">
                        <div className={`font-bold ${ticker?.dir === "up" ? "text-emerald-400" : ticker?.dir === "down" ? "text-rose-400" : "text-slate-200"}`}>
                          ${livePrice < 0.01 ? livePrice.toFixed(6) : livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                        </div>
                        <div className="text-[10px] text-slate-500 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                          <span>Live Binance</span>
                        </div>
                      </td>

                      {/* Margin / Size */}
                      <td className="p-3.5 font-mono">
                        <div className="font-bold text-white">${(trade.margin_usd ?? trade.notional_usd).toFixed(2)}</div>
                        <div className="text-[10px] text-slate-500">Notional: ${trade.notional_usd.toFixed(2)}</div>
                      </td>

                      {/* Unrealized PnL */}
                      <td className="p-3.5 font-mono">
                        <div className={`font-bold flex items-center gap-1 ${pnlUsd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          <span>{pnlUsd >= 0 ? "+" : ""}${pnlUsd.toFixed(2)}</span>
                          <span className="text-[10px]">({pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%)</span>
                        </div>
                        <div className="text-[10px] text-slate-500">
                          ROE: {trade.roe_pct !== undefined ? `${trade.roe_pct >= 0 ? "+" : ""}${trade.roe_pct.toFixed(2)}%` : "—"}
                        </div>
                      </td>

                      {/* SL / TP Gates */}
                      <td className="p-3.5 font-mono text-[11px]">
                        <div className="text-rose-400">
                          SL: {trade.stop_loss ? `$${trade.stop_loss < 0.01 ? trade.stop_loss.toFixed(6) : trade.stop_loss.toLocaleString()}` : "Trailing (1%)"}
                        </div>
                        <div className="text-emerald-400">
                          TP: {trade.take_profit ? `$${trade.take_profit < 0.01 ? trade.take_profit.toFixed(6) : trade.take_profit.toLocaleString()}` : "Discretionary"}
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="p-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => onOpenAdjust(trade)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                            title="Adjust Stop-Loss & Take-Profit"
                          >
                            <Sliders className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => onCloseTrade(trade.trade_id)}
                            disabled={actionLoadingId === trade.trade_id}
                            className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold transition-all flex items-center gap-1 active:scale-95 disabled:opacity-50"
                            title="Close Position & Return Capital"
                          >
                            <Trash2 className="w-3 h-3 text-rose-400" />
                            <span>{actionLoadingId === trade.trade_id ? "Closing..." : trade.market_type === "SPOT" ? "Sell Spot" : "Close"}</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
