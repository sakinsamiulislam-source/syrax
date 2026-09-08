import React, { useState, useEffect } from "react";
import {
  Clock,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  X,
  Lock,
  ArrowRight,
  TrendingUp,
  Percent,
  Layers,
  Terminal,
  ShieldAlert,
  Loader2
} from "lucide-react";
import { OrderTicketCardData } from "@/types";
import { api } from "@/lib/api";

function formatCryptoPrice(price: number | undefined | null): string {
  if (price === undefined || price === null || isNaN(price)) return "N/A";
  if (price === 0) return "$0.00";
  if (price < 0.01) return `$${price.toFixed(8)}`;
  if (price < 1) return `$${price.toFixed(4)}`;
  return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

interface OrderTicketCardProps {
  ticket: OrderTicketCardData;
  onConfirmed?: (result: any) => void;
  onCancelled?: (result: any) => void;
  onInjectPrompt?: (cmd: string) => void;
}

export const OrderTicketCard: React.FC<OrderTicketCardProps> = ({
  ticket: initialTicket,
  onConfirmed,
  onCancelled,
  onInjectPrompt,
}) => {
  const [ticket, setTicket] = useState<OrderTicketCardData>(initialTicket);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(() => {
    const now = Date.now() / 1000;
    return Math.max(0, Math.round(initialTicket.expires_at - now));
  });
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Sync state if prop changes
  useEffect(() => {
    setTicket(initialTicket);
    const now = Date.now() / 1000;
    setRemainingSeconds(Math.max(0, Math.round(initialTicket.expires_at - now)));
  }, [initialTicket]);

  // Live Countdown Timer
  useEffect(() => {
    if (ticket.status !== "PENDING_CONFIRMATION" || remainingSeconds <= 0) return;

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setTicket((t) => ({ ...t, status: "EXPIRED" }));
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [ticket.status, remainingSeconds]);

  const handleCopyHash = () => {
    navigator.clipboard.writeText(ticket.ticket_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyCmd = () => {
    navigator.clipboard.writeText(ticket.confirmation_command);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2000);
  };

  const handleConfirmClick = async () => {
    if (remainingSeconds <= 0 || ticket.status !== "PENDING_CONFIRMATION" || actionLoading) return;
    setActionLoading(true);
    setActionError(null);

    try {
      const res = await api.confirmTicket(ticket.parent_order_id, ticket.confirmation_command);
      if (res.decision === "CONFIRMATION_REJECTED" || res.success === false) {
        setActionError(res.reason || res.explanation || "Confirmation rejected.");
        setTicket((t) => ({ ...t, status: res.ticket_status || "REJECTED_BY_GATEWAY" }));
      } else {
        setTicket((t) => ({ ...t, status: "EXECUTED" }));
        if (onConfirmed) onConfirmed(res);
      }
    } catch (err: any) {
      setActionError(err.message || "Network error during ticket confirmation.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelClick = async () => {
    if (ticket.status !== "PENDING_CONFIRMATION" || actionLoading) return;
    setActionLoading(true);
    setActionError(null);

    try {
      const res = await api.cancelTicket(ticket.parent_order_id);
      setTicket((t) => ({ ...t, status: "CANCELLED" }));
      if (onCancelled) onCancelled(res);
    } catch (err: any) {
      setActionError(err.message || "Network error cancelling ticket.");
    } finally {
      setActionLoading(false);
    }
  };

  const isPending = ticket.status === "PENDING_CONFIRMATION" && remainingSeconds > 0;
  const isExpired = ticket.status === "EXPIRED" || (ticket.status === "PENDING_CONFIRMATION" && remainingSeconds === 0);
  const isExecuted = ticket.status === "EXECUTED" || ticket.status === "CONFIRMED";
  const isRejected = ticket.status === "REJECTED_BY_GATEWAY" || ticket.status === "INVALIDATED";
  const isCancelled = ticket.status === "CANCELLED";

  const isBuy = ticket.side.toUpperCase() === "BUY" || ticket.side.toUpperCase() === "LONG";
  const isFutures = ticket.market_type.toUpperCase() === "FUTURES";

  const getStatusBadge = () => {
    if (isPending) {
      return (
        <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 animate-pulse">
          <Clock className="w-3.5 h-3.5" />
          AWAITING EXACT CONFIRMATION ({remainingSeconds}s)
        </span>
      );
    }
    if (isExecuted) {
      return (
        <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" />
          CONFIRMED & ROUTED TO GATEWAY
        </span>
      );
    }
    if (isExpired) {
      return (
        <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          TTL EXPIRED (INACTIVE)
        </span>
      );
    }
    if (isCancelled) {
      return (
        <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5">
          <X className="w-3.5 h-3.5" />
          CANCELLED BY USER
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center gap-1.5">
        <AlertTriangle className="w-3.5 h-3.5" />
        {ticket.status}
      </span>
    );
  };

  const getEnvBadge = () => {
    const env = (ticket.environment || "SIMULATED").toUpperCase();
    if (env === "LIVE") {
      return { label: "LIVE BINANCE", style: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" };
    }
    if (env === "TESTNET") {
      return { label: "BINANCE TESTNET", style: "bg-amber-500/15 text-amber-300 border-amber-500/30" };
    }
    return { label: "SIMULATED [LIVE FEEDS]", style: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30" };
  };

  const envBadge = getEnvBadge();

  return (
    <div
      className={`rounded-xl bg-[#090D16] border ${
        isPending
          ? "border-amber-500/40 shadow-lg shadow-amber-950/20"
          : isExecuted
          ? "border-emerald-500/40 shadow-lg shadow-emerald-950/20"
          : "border-slate-800"
      } overflow-hidden transition-all text-slate-200`}
    >
      {/* Top Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-slate-900 via-slate-900/90 to-slate-950 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-mono font-bold">
            <Layers className="w-3.5 h-3.5" />
            <span>EXACT ORDER TICKET</span>
          </div>
          <span className="font-mono font-bold text-white text-sm tracking-wider">
            {ticket.parent_order_id}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${envBadge.style}`}>
            {envBadge.label}
          </span>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
            Scope: {ticket.account_scope || "default"}
          </span>
        </div>

        <div className="flex items-center gap-2">{getStatusBadge()}</div>
      </div>

      {/* Main Ticket Body */}
      <div className="p-4 space-y-4">
        {/* Core Instrument Header */}
        <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2.5">
            <span
              className={`px-2.5 py-1 rounded text-xs font-bold font-mono tracking-wider ${
                isBuy
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
              }`}
            >
              {ticket.side.toUpperCase()}
            </span>
            <span className="text-base font-bold font-mono text-white tracking-wide">
              {ticket.symbol}
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase font-mono">
              {ticket.order_type}
            </span>
            {isFutures && (
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">
                {ticket.leverage}x LEVERAGE
              </span>
            )}
          </div>

          <div className="text-right font-mono">
            <span className="text-[10px] text-slate-400 block uppercase">Notional Value</span>
            <span className="text-sm font-bold text-white">${ticket.notional_usd.toFixed(2)} USD</span>
            {ticket.quantity !== undefined && ticket.quantity > 0 && (
              <span className="text-[10px] text-slate-400 block">({ticket.quantity} units)</span>
            )}
          </div>
        </div>

        {/* Financial & Safety Parameters Matrix */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
          <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
            <span className="text-[10px] text-slate-400 block font-sans font-medium">Decision Mid Price</span>
            <span className="text-xs font-bold text-white">
              {formatCryptoPrice(ticket.decision_price)}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
            <span className="text-[10px] text-slate-400 block font-sans font-medium">Limit Execution Price</span>
            <span className="text-xs font-bold text-cyan-300">
              {ticket.limit_price ? formatCryptoPrice(ticket.limit_price) : "Market / Best Bid-Ask"}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/30">
            <span className="text-[10px] text-rose-300 block font-sans font-medium flex items-center justify-between">
              <span>Mandatory Stop Loss</span>
              <ShieldAlert className="w-3 h-3 text-rose-400" />
            </span>
            <span className="text-xs font-bold text-rose-400">
              {formatCryptoPrice(ticket.stop_loss)}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/30">
            <span className="text-[10px] text-emerald-300 block font-sans font-medium">Take Profit Target</span>
            <span className="text-xs font-bold text-emerald-400">
              {ticket.take_profit ? formatCryptoPrice(ticket.take_profit) : "Manual / Trailing"}
            </span>
          </div>
        </div>

        {/* Risk Gating, Fee Breakdown & Total Balance Deduction */}
        {(() => {
          const marginRequired = (isFutures && ticket.leverage > 1) ? (ticket.notional_usd / ticket.leverage) : ticket.notional_usd;
          const estFee = ticket.estimated_fee_usd !== undefined ? ticket.estimated_fee_usd : (ticket.notional_usd * (isFutures ? 0.0005 : 0.001));
          const totalDeduction = marginRequired + estFee;
          const feeRateStr = ticket.fee_rate_str || (isFutures ? "0.05% Futures Taker" : "0.10% Spot Taker");

          return (
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/90 space-y-2.5 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
                <div className="flex items-center gap-1.5 text-indigo-300 bg-slate-900/60 p-2 rounded border border-slate-800">
                  <Lock className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <div>
                    <span className="text-slate-400 block text-[10px]">Risk Limit:</span>
                    <span><strong>${ticket.risk_amount_usd.toFixed(2)} USD</strong> ({ticket.risk_pct}% Cap)</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-amber-300 bg-slate-900/60 p-2 rounded border border-slate-800">
                  <Percent className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <div>
                    <span className="text-slate-400 block text-[10px]">Estimated Fee:</span>
                    <span><strong>${estFee.toFixed(4)} USDT</strong> ({feeRateStr})</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-emerald-300 bg-emerald-950/20 p-2 rounded border border-emerald-500/30">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <div>
                    <span className="text-emerald-400/80 block text-[10px] font-bold">Total Cash Deduction:</span>
                    <span><strong>${totalDeduction.toFixed(4)} USD</strong> (Margin + Fee)</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-slate-900 text-[10px] text-slate-400 font-mono">
                <span className="text-slate-400">ℹ️ <em>Trading fee is automatically deducted from liquid cash upon order execution.</em></span>
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">SHA-256:</span>
                  <span className="text-slate-300 truncate max-w-[120px] sm:max-w-[200px]" title={ticket.ticket_hash}>
                    {ticket.ticket_hash ? ticket.ticket_hash : "UNHASHED"}
                  </span>
                  <button
                    onClick={handleCopyHash}
                    className="p-1 hover:text-white transition-colors"
                    title="Copy Full SHA-256 Hash"
                  >
                    {copiedHash ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
                  </button>
                </div>
              </div>
            </div>
          );
        })()}


        {/* Error / Alert Message */}
        {actionError && (
          <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{actionError}</span>
          </div>
        )}

        {/* Exact Confirmation Interaction Boundary */}
        {isPending && (
          <div className="pt-2 border-t border-slate-800 space-y-3">
            <div className="p-3 rounded-xl bg-gradient-to-r from-amber-950/30 via-slate-900/60 to-slate-950 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold text-amber-300 uppercase tracking-wider block">
                  Exact Confirmation Token Required
                </span>
                <p className="text-xs text-slate-300 mt-0.5">
                  Type or click below to authorize atomic gateway routing:
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <code className="px-2 py-0.5 rounded bg-black/60 border border-amber-500/40 text-amber-400 font-mono font-bold text-xs tracking-wider">
                    {ticket.confirmation_command}
                  </code>
                  <button
                    onClick={handleCopyCmd}
                    className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
                  >
                    {copiedCmd ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedCmd ? "Copied" : "Copy"}</span>
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={handleCancelClick}
                  disabled={actionLoading}
                  className="px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold transition-all active:scale-95 disabled:opacity-50 flex items-center gap-1.5"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Dismiss</span>
                </button>

                <button
                  onClick={handleConfirmClick}
                  disabled={actionLoading || remainingSeconds <= 0}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono font-bold text-xs shadow-md shadow-emerald-950/40 border border-emerald-400/40 flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Verifying & Executing...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{ticket.confirmation_command}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Expired State Warning */}
        {isExpired && (
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <span>Ticket has expired. A new command is required to generate a fresh ticket.</span>
            {onInjectPrompt && (
              <button
                onClick={() => onInjectPrompt(`Buy $${ticket.notional_usd} ${ticket.symbol}`)}
                className="text-indigo-400 hover:text-indigo-300 font-semibold font-mono"
              >
                Regenerate Ticket &rarr;
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
