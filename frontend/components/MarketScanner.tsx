import React from "react";
import { TrendingUp, RefreshCw, Filter, Search, Zap } from "lucide-react";
import { Opportunity } from "@/types";

interface MarketScannerProps {
  opportunities: Opportunity[];
  category: "ALL" | "FUTURES" | "ALPHA" | "SPOT";
  onCategoryChange: (cat: "ALL" | "FUTURES" | "ALPHA" | "SPOT") => void;
  categoryLoading: boolean;
  verdictFilter: "ALL" | "TRADEABLE" | "WATCH" | "TRAP";
  setVerdictFilter: (v: "ALL" | "TRADEABLE" | "WATCH" | "TRAP") => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  onSearch: (q: string) => void;
  searchLoading: boolean;
  onSelectCoin: (coin: Opportunity) => void;
  liveTickerMap: Record<string, { price: number; dir: "up" | "down" | null; change24h?: number; lastUpdate: number }>;
}

export const MarketScanner: React.FC<MarketScannerProps> = ({
  opportunities,
  category,
  onCategoryChange,
  categoryLoading,
  verdictFilter,
  setVerdictFilter,
  searchQuery,
  setSearchQuery,
  onSearch,
  searchLoading,
  onSelectCoin,
  liveTickerMap,
}) => {
  const quickTokens = ["1000PEPE", "PNUT", "NEIRO", "SOL", "SUI", "DOGE", "BTC", "ETH", "PUMP"];

  const filteredCoins = opportunities.filter((c) => {
    if (verdictFilter !== "ALL" && c.label !== verdictFilter) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Binance Market & Liquidity Scanner</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              LIVE REST
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time orderbook depth, bid-ask spread in bps, and AI opportunity scoring.
          </p>
        </div>

        {/* Verdict Filters */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <span className="text-[11px] text-slate-400 px-2 font-medium">Verdict:</span>
          {(["ALL", "TRADEABLE", "WATCH", "TRAP"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setVerdictFilter(v)}
              className={`px-2.5 py-1 rounded font-semibold transition-all ${
                verdictFilter === v ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Category Pills & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs overflow-x-auto">
          {[
            { id: "ALL", label: "Unified Markets" },
            { id: "FUTURES", label: "USDⓈ-M Perps" },
            { id: "ALPHA", label: "Alpha Breakouts" },
            { id: "SPOT", label: "Spot Bluechips" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => onCategoryChange(cat.id as any)}
              disabled={categoryLoading}
              className={`px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                category === cat.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>{cat.label}</span>
              {category === cat.id && categoryLoading && <RefreshCw className="w-3 h-3 animate-spin" />}
            </button>
          ))}
        </div>

        {/* Live Search Input */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch(searchQuery)}
            placeholder="Search any Binance pair (e.g. SOL, SUI, PUMP)..."
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500 w-full sm:w-64"
          />
          <button
            onClick={() => onSearch(searchQuery)}
            disabled={searchLoading}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shrink-0 transition-colors"
          >
            {searchLoading ? "Fetching..." : "Search"}
          </button>
        </div>
      </div>

      {/* Quick Tag Pills */}
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="text-[11px] text-slate-500 font-medium">Quick Pairs:</span>
        {quickTokens.map((t) => (
          <button
            key={t}
            onClick={() => {
              setSearchQuery(t);
              onSearch(t);
            }}
            className="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-[11px] font-mono transition-colors"
          >
            {t}
          </button>
        ))}
      </div>

      {/* Markets Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0A0F1D] overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-medium">
              <tr>
                <th className="p-3.5">Symbol</th>
                <th className="p-3.5">Live Price</th>
                <th className="p-3.5">24h Change</th>
                <th className="p-3.5">Trend & Momentum</th>
                <th className="p-3.5">Spread (bps)</th>
                <th className="p-3.5">Liquidity</th>
                <th className="p-3.5">AI Score</th>
                <th className="p-3.5">Verdict</th>
                <th className="p-3.5 text-right">Interactive Chart & Evaluation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredCoins.map((coin) => {
                const isPerp = coin.market_type === "FUTURES" || coin.symbol.startsWith("1000");
                const ticker = liveTickerMap[coin.symbol];
                const livePrice = ticker ? ticker.price : coin.last_price;
                const liveDir = ticker ? ticker.dir : null;
                const liveChange = ticker?.change24h ?? coin.change_24h;

                return (
                  <tr
                    key={coin.symbol}
                    onClick={() => onSelectCoin(coin)}
                    className="hover:bg-slate-800/60 cursor-pointer transition-colors group"
                    title={`Click to view live Binance chart and evaluate ${coin.symbol}`}
                  >
                    {/* Symbol */}
                    <td className="p-3.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white font-mono group-hover:text-indigo-400 transition-colors flex items-center gap-1.5">
                          {coin.symbol}
                          <TrendingUp className="w-3.5 h-3.5 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </span>
                        {isPerp && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                            PERP
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 group-hover:text-slate-400">
                        {isPerp ? "USDⓈ-M Futures" : "Binance Spot"} • <span className="text-indigo-400 font-medium">Click to view chart</span>
                      </div>
                    </td>

                    {/* Price */}
                    <td className="p-3.5 font-mono font-bold">
                      <span className={liveDir === "up" ? "text-emerald-400" : liveDir === "down" ? "text-rose-400" : "text-white"}>
                        ${livePrice < 0.01
                          ? livePrice.toFixed(6)
                          : livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                      </span>
                    </td>

                    {/* 24h Change */}
                    <td className="p-3.5 font-mono font-bold">
                      <span className={liveChange >= 0 ? "text-emerald-400" : "text-rose-400"}>
                        {liveChange >= 0 ? "+" : ""}{liveChange.toFixed(2)}%
                      </span>
                    </td>

                    {/* Trend */}
                    <td className="p-3.5 text-slate-300">
                      <div className="font-medium">{coin.trend.replace("_", " ")}</div>
                      <div className="text-[10px] text-slate-500">{coin.momentum}</div>
                    </td>

                    {/* Spread */}
                    <td className="p-3.5 font-mono text-slate-300">
                      <span className={coin.spread_bps > 5 ? "text-rose-400 font-bold" : "text-slate-300"}>
                        {coin.spread_bps} bps
                      </span>
                    </td>

                    {/* Liquidity */}
                    <td className="p-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          coin.liquidity_quality === "HIGH"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                        }`}
                      >
                        {coin.liquidity_quality}
                      </span>
                    </td>

                    {/* AI Score */}
                    <td className="p-3.5 font-mono font-bold text-indigo-400">
                      {coin.ai_score}/100
                    </td>

                    {/* Label */}
                    <td className="p-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          coin.label === "TRADEABLE"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : coin.label === "WATCH"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {coin.label}
                      </span>
                    </td>

                    {/* Action */}
                    <td className="p-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCoin(coin);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md hover:shadow-indigo-500/25 flex items-center gap-1.5 ml-auto"
                      >
                        <TrendingUp className="w-3.5 h-3.5" />
                        <span>Evaluate & Chart</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
