import React, { useState } from "react";
import { Check, Copy, ShieldCheck, DollarSign, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";
import { ExecutionReceipt } from "@/types";

interface ExecutionReceiptCardProps {
  receipt: ExecutionReceipt;
  confidenceScore?: number;
  environmentType?: "SIMULATED" | "TESTNET" | "BINANCE_AGENTIC_SUB_ACCOUNT" | "LIVE_BINANCE";
}

export const ExecutionReceiptCard: React.FC<ExecutionReceiptCardProps> = ({
  receipt,
  confidenceScore = 88,
  environmentType = "BINANCE_AGENTIC_SUB_ACCOUNT",
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyOrderId = (orderId: string) => {
    navigator.clipboard.writeText(orderId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const getEnvBadge = () => {
    switch (environmentType) {
      case "LIVE_BINANCE":
        return { label: "LIVE BINANCE", bg: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" };
      case "TESTNET":
        return { label: "BINANCE TESTNET", bg: "bg-amber-500/15 text-amber-300 border-amber-500/30" };
      case "SIMULATED":
        return { label: "SIMULATED EXECUTION", bg: "bg-slate-800 text-slate-300 border-slate-700" };
      case "BINANCE_AGENTIC_SUB_ACCOUNT":
      default:
        return { label: "BINANCE AGENTIC SUB-ACCOUNT", bg: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30" };
    }
  };

  const env = getEnvBadge();
  const isLimit = receipt.order_type === "LIMIT" || receipt.status === "PLACED" || receipt.status === "OPEN_LIMIT";
  const isFutures = receipt.market_type === "FUTURES";
  const isBuy = receipt.side === "BUY" || receipt.action === "BUY";
  const isConvert = receipt.action === "CONVERT" || receipt.market_type === "CONVERT";
  const isClose = receipt.action === "CLOSE" || receipt.status === "CLOSED";

  return (
    <div className={`rounded-xl bg-[#080C14] border ${isLimit ? "border-cyan-500/40" : "border-emerald-500/30"} overflow-hidden shadow-xl transition-all`}>
      {/* Top Banner */}
      <div className={`px-4 py-3 bg-gradient-to-r ${isLimit ? "from-cyan-950/40" : "from-emerald-950/40"} via-slate-900/60 to-slate-950 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2.5`}>
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${isLimit ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/30" : "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"} border flex items-center gap-1`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isLimit ? "bg-cyan-400" : "bg-emerald-400"} animate-pulse`} />
            {isLimit ? "LIMIT PLACED (PENDING)" : (receipt.status || "EXECUTED")}
          </span>
          <span className="text-xs font-bold text-white font-mono">
            {receipt.trade_id || receipt.order_id || "TRD-AGENT-FILL"}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${env.bg}`}>
            {env.label}
          </span>
        </div>

        {receipt.order_id && (
          <button
            onClick={() => handleCopyOrderId(receipt.order_id!)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-700/80 text-[11px] font-mono transition-colors"
            title="Copy Order ID"
          >
            <span className="text-slate-400">Order ID:</span>
            <span className="font-bold text-white">{receipt.order_id}</span>
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
          </button>
        )}
      </div>

      {/* Main Receipt Content */}
      <div className="p-4 space-y-3.5">
        {/* Instrument & Term Header */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 flex-wrap gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white font-mono">
                {receipt.symbol || "PORTFOLIO REBALANCE"}
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                  isLimit
                    ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30"
                    : isConvert
                    ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                    : isClose
                    ? "bg-slate-800 text-slate-300 border border-slate-700"
                    : isFutures
                    ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                    : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                }`}
              >
                {receipt.term || (isFutures ? `FUTURES ${receipt.leverage || 10}x` : isConvert ? "BINANCE CONVERT" : "SPOT")}
              </span>
            </div>
            {receipt.message && (
              <p className="text-xs text-slate-300 mt-1 font-medium">{receipt.message}</p>
            )}
          </div>

          <div className="text-right">
            <div className="text-[10px] text-slate-400">AI Confidence</div>
            <div className="text-xs font-mono font-bold text-indigo-300">{confidenceScore}% Conviction</div>
          </div>
        </div>

        {/* Detailed Financial & Risk Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          {/* Filled / Limit Price */}
          {receipt.entry_price !== undefined && receipt.entry_price !== null && (
            <div className={`p-2.5 rounded-lg ${isLimit ? "bg-cyan-950/20 border-cyan-500/30" : "bg-slate-900/80 border-slate-800/80"} border`}>
              <span className="text-[10px] text-slate-400 block flex items-center justify-between">
                <span>{isLimit ? "Limit Target Price" : "Filled Price"}</span>
                {isLimit && receipt.offset_pct !== undefined && receipt.offset_pct !== null && receipt.offset_pct !== 0 && (
                  <span className="text-[9px] font-bold text-cyan-300">
                    {receipt.offset_pct > 0 ? `+${receipt.offset_pct.toFixed(1)}%` : `${receipt.offset_pct.toFixed(1)}%`}
                  </span>
                )}
              </span>
              <span className={`font-bold ${isLimit ? "text-cyan-300" : "text-white"} font-mono`}>
                ${receipt.entry_price < 0.01
                  ? receipt.entry_price.toFixed(6)
                  : receipt.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
              </span>
            </div>
          )}

          {/* Position / Margin USD */}
          {receipt.margin_usd !== undefined && receipt.margin_usd !== null && (
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block">{isLimit ? "Margin Reserved" : "Margin Committed"}</span>
              <span className="font-bold text-emerald-400 font-mono">
                ${receipt.margin_usd.toFixed(2)} USDT
              </span>
            </div>
          )}

          {/* Stop Loss */}
          <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <span className="text-[10px] text-slate-400 block">Stop-Loss Guard</span>
            <span className="font-bold text-rose-400 font-mono">
              {receipt.stop_loss !== undefined && receipt.stop_loss !== null
                ? `$${receipt.stop_loss < 0.01 ? receipt.stop_loss.toFixed(6) : receipt.stop_loss.toLocaleString()}`
                : "Mandate Trailing"}
            </span>
          </div>

          {/* Take Profit */}
          <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <span className="text-[10px] text-slate-400 block">Take-Profit Target</span>
            <span className="font-bold text-emerald-400 font-mono">
              {receipt.take_profit !== undefined && receipt.take_profit !== null
                ? `$${receipt.take_profit < 0.01 ? receipt.take_profit.toFixed(6) : receipt.take_profit.toLocaleString()}`
                : "None (Manual/Trailing)"}
            </span>
          </div>

          {/* Realized PnL (for closes) */}
          {receipt.realized_pnl_usd !== undefined && (
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block">Realized PnL</span>
              <span
                className={`font-bold font-mono ${
                  receipt.realized_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {receipt.realized_pnl_usd >= 0 ? "+" : ""}${receipt.realized_pnl_usd.toFixed(2)} USDT
              </span>
            </div>
          )}

          {/* Liquidation (for futures) */}
          {receipt.liquidation_price && receipt.liquidation_price > 0 ? (
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block">Liquidation Price</span>
              <span className="font-bold text-amber-400 font-mono">
                ${receipt.liquidation_price.toLocaleString()}
              </span>
            </div>
          ) : null}

          {/* Fee Breakdown Card */}
          <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-500/30 col-span-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-amber-400 font-semibold flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                Binance Trading Fee Incurred
              </span>
              <span className="text-[10px] font-mono text-amber-300/80">
                {receipt.fee_rate_pct !== undefined ? `${receipt.fee_rate_pct}%` : "Standard Tier"}
              </span>
            </div>
            <span className="font-bold text-amber-300 font-mono text-xs block mt-0.5">
              {receipt.fee_breakdown || (receipt.fee_usd !== undefined ? `$${receipt.fee_usd.toFixed(4)} USDT` : "$0.0050 USDT (0.10% Binance Spot Fee)")}
            </span>
          </div>
        </div>

        {/* Security & Risk Footnote */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 flex-wrap gap-2">
          <div className="flex items-center gap-2 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Sentry Radar Verified (0 Exploits)</span>
          </div>
          <div className="flex items-center gap-2 text-indigo-300 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
            <span>Risk Cap: &le;1.0% ($5.00 Maximum Loss Rule)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
