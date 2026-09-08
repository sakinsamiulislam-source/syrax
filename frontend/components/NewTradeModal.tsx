import React, { useState } from "react";
import { Plus, X, Shield, DollarSign } from "lucide-react";

interface NewTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (trade: {
    symbol: string;
    side: "BUY" | "SELL";
    amount: number;
    marketType: "SPOT" | "FUTURES" | "MARGIN";
    leverage: number;
    marginType: "ISOLATED" | "CROSS";
    stopLoss?: number;
    takeProfit?: number;
  }) => void;
  loading: boolean;
}

export const NewTradeModal: React.FC<NewTradeModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  loading,
}) => {
  const [symbol, setSymbol] = useState("SOLUSDT");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [amount, setAmount] = useState(25);
  const [marketType, setMarketType] = useState<"SPOT" | "FUTURES" | "MARGIN">("FUTURES");
  const [leverage, setLeverage] = useState(10);
  const [marginType, setMarginType] = useState<"ISOLATED" | "CROSS">("ISOLATED");
  const [stopLoss, setStopLoss] = useState("");
  const [takeProfit, setTakeProfit] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !amount) return;
    onSubmit({
      symbol: symbol.toUpperCase(),
      side,
      amount,
      marketType,
      leverage: marketType === "SPOT" ? 1 : leverage,
      marginType,
      stopLoss: stopLoss ? parseFloat(stopLoss) : undefined,
      takeProfit: takeProfit ? parseFloat(takeProfit) : undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-2xl bg-[#0C1222] border border-indigo-500/40 max-w-md w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Plus className="w-4 h-4 text-indigo-400" />
            <span>Open Sub-Wallet Position</span>
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          {/* Symbol */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Trading Pair</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="e.g. SOLUSDT, BTCUSDT, PUMPUSDT"
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono uppercase outline-none focus:border-indigo-500"
              required
            />
          </div>

          {/* Market & Side */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Market Type</label>
              <select
                value={marketType}
                onChange={(e) => setMarketType(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white outline-none focus:border-indigo-500"
              >
                <option value="FUTURES">Futures (USDⓈ-M)</option>
                <option value="SPOT">Binance Spot</option>
                <option value="MARGIN">Isolated Margin</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Side</label>
              <div className="flex rounded-lg overflow-hidden border border-slate-800">
                <button
                  type="button"
                  onClick={() => setSide("BUY")}
                  className={`flex-1 py-2 font-bold transition-colors ${
                    side === "BUY" ? "bg-emerald-600 text-white" : "bg-slate-900 text-slate-400"
                  }`}
                >
                  BUY / LONG
                </button>
                <button
                  type="button"
                  onClick={() => setSide("SELL")}
                  className={`flex-1 py-2 font-bold transition-colors ${
                    side === "SELL" ? "bg-rose-600 text-white" : "bg-slate-900 text-slate-400"
                  }`}
                >
                  SELL / SHORT
                </button>
              </div>
            </div>
          </div>

          {/* Margin Amount */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Margin Budget (USDT)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              min="1"
              max="500"
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono outline-none focus:border-indigo-500"
              required
            />
          </div>

          {/* Leverage (if Futures) */}
          {marketType === "FUTURES" && (
            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>Leverage</span>
                <span className="text-amber-400 font-mono font-bold">{leverage}x Isolated</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={leverage}
                onChange={(e) => setLeverage(parseInt(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>
          )}

          {/* SL / TP */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Stop Loss ($) (Optional)</label>
              <input
                type="number"
                step="any"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                placeholder="Optional"
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Take Profit ($) (Optional)</label>
              <input
                type="number"
                step="any"
                value={takeProfit}
                onChange={(e) => setTakeProfit(e.target.value)}
                placeholder="Optional"
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-sm"
            >
              {loading ? "Placing..." : "Place Order"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
