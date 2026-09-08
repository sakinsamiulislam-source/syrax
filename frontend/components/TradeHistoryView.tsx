import React, { useState } from "react";
import { Clock, Search, Filter, Copy, Check, DollarSign, ArrowUpRight, ArrowDownRight, CheckCircle2 } from "lucide-react";
import { TradeHistoryItem } from "@/types";

interface TradeHistoryViewProps {
  tradeHistory: TradeHistoryItem[];
  filter: "ALL" | "SPOT" | "FUTURES" | "CONVERT" | "BUY" | "SELL";
  setFilter: (f: "ALL" | "SPOT" | "FUTURES" | "CONVERT" | "BUY" | "SELL") => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  onRefresh: () => void;
}

export const TradeHistoryView: React.FC<TradeHistoryViewProps> = ({
  tradeHistory,
  filter,
  setFilter,
  searchQuery,
  setSearchQuery,
  onRefresh,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const filteredHistory = tradeHistory.filter((item) => {
    if (filter === "SPOT" && item.market_type !== "SPOT") return false;
    if (filter === "FUTURES" && item.market_type !== "FUTURES") return false;
    if (filter === "CONVERT" && item.market_type !== "CONVERT" && item.type !== "CONVERT") return false;
    if (filter === "BUY" && item.side !== "BUY") return false;
    if (filter === "SELL" && item.side !== "SELL") return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.symbol.toLowerCase().includes(q) ||
        item.order_id.toLowerCase().includes(q) ||
        item.trade_id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>Execution Journal & Trade Receipts</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Complete cryptographic audit trail of all sub-wallet fills, fees, and order IDs.
          </p>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search symbol or Order ID..."
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500 w-48"
            />
          </div>

          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            {(["ALL", "SPOT", "FUTURES", "CONVERT"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded font-semibold transition-all ${
                  filter === f ? "bg-slate-700 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* History Table */}
      {filteredHistory.length === 0 ? (
        <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-1">
          <Clock className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">No trade records found</p>
          <p className="text-xs text-slate-500">
            Executed trades, fee breakdowns, and order IDs will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-[#0A0F1D] overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-medium">
                <tr>
                  <th className="p-3.5">Order ID & Timestamp</th>
                  <th className="p-3.5">Instrument</th>
                  <th className="p-3.5">Market & Term</th>
                  <th className="p-3.5">Filled Price</th>
                  <th className="p-3.5">Margin / Notional</th>
                  <th className="p-3.5">Fee Breakdown</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Realized PnL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredHistory.map((item) => {
                  const isBuy = item.side === "BUY";
                  const isFutures = item.market_type === "FUTURES";
                  const isConvert = item.market_type === "CONVERT";

                  return (
                    <tr key={item.order_id || item.trade_id} className="hover:bg-slate-800/30 transition-colors">
                      {/* Order ID */}
                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-indigo-300">{item.order_id}</span>
                          <button
                            onClick={() => handleCopy(item.order_id)}
                            className="text-slate-500 hover:text-slate-300 transition-colors"
                            title="Copy Order ID"
                          >
                            {copiedId === item.order_id ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">{item.timestamp}</div>
                      </td>

                      {/* Instrument */}
                      <td className="p-3.5">
                        <span className="font-bold text-white font-mono">{item.symbol}</span>
                      </td>

                      {/* Term */}
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isConvert
                              ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/20"
                              : isFutures
                              ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                              : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                          }`}
                        >
                          {item.term || item.side}
                        </span>
                      </td>

                      {/* Price */}
                      <td className="p-3.5 font-mono font-medium text-slate-200">
                        ${item.price < 0.01
                          ? item.price.toFixed(6)
                          : item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                      </td>

                      {/* Margin */}
                      <td className="p-3.5 font-mono">
                        <div className="font-bold text-white">${(item.margin_usd ?? item.notional_usd ?? 0).toFixed(2)}</div>
                        <div className="text-[10px] text-slate-500">{item.quantity?.toFixed(4)} qty</div>
                      </td>

                      {/* Fee */}
                      <td className="p-3.5 font-mono">
                        <span className="text-amber-300 font-medium">
                          {item.fee_breakdown || `$${item.fee_usd.toFixed(4)} USDT`}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {item.status}
                        </span>
                      </td>

                      {/* Realized PnL */}
                      <td className="p-3.5 text-right font-mono font-bold">
                        {item.realized_pnl_usd !== undefined ? (
                          <span className={item.realized_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}>
                            {item.realized_pnl_usd >= 0 ? "+" : ""}${item.realized_pnl_usd.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
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
