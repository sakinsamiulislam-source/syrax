"use client";

import React, { useState } from "react";
import {
  X,
  ArrowRightLeft,
  ArrowDown,
  Shield,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Coins,
  Wallet,
  Sparkles,
  Zap,
  TrendingUp,
  Layers,
  PieChart,
  Lock
} from "lucide-react";
import { WalletsSummaryData, WalletItemData } from "@/types";
import { api } from "@/lib/api";

interface InternalTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  walletsData: WalletsSummaryData | null;
  onRefresh: () => void;
  initialFromWallet?: string;
  initialToWallet?: string;
}

const WALLET_OPTIONS = [
  { id: "SPOT", name: "Fiat & Spot", icon: Wallet, color: "text-amber-400" },
  { id: "FUNDING", name: "Funding Wallet", icon: Coins, color: "text-emerald-400" },
  { id: "USDT_FUTURES", name: "USD(S)-M Futures", icon: TrendingUp, color: "text-cyan-400" },
  { id: "COIN_FUTURES", name: "Coin-M Futures", icon: Zap, color: "text-indigo-400" },
  { id: "CROSS_MARGIN", name: "Cross Margin (3x/5x)", icon: Layers, color: "text-purple-400" },
];

export const InternalTransferModal: React.FC<InternalTransferModalProps> = ({
  isOpen,
  onClose,
  walletsData,
  onRefresh,
  initialFromWallet = "SPOT",
  initialToWallet = "USDT_FUTURES",
}) => {
  const [fromWallet, setFromWallet] = useState(initialFromWallet);
  const [toWallet, setToWallet] = useState(initialToWallet);
  const [selectedAsset, setSelectedAsset] = useState("USDT");
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<any | null>(null);

  if (!isOpen) return null;

  // Find source wallet data
  const currentSrcWallet = walletsData?.wallets?.find((w) => w.wallet_id === fromWallet);
  const currentDestWallet = walletsData?.wallets?.find((w) => w.wallet_id === toWallet);

  // Available assets in source wallet
  const srcAssets = currentSrcWallet?.assets || [];
  const activeAssetBal = srcAssets.find((a) => a.asset === selectedAsset)?.free || 0;

  const handleSwap = () => {
    const temp = fromWallet;
    setFromWallet(toWallet);
    setToWallet(temp);
    setError(null);
  };

  const handleQuickPct = (pct: number) => {
    if (activeAssetBal <= 0) return;
    const calc = (activeAssetBal * pct).toFixed(selectedAsset === "USDT" || selectedAsset === "USDC" ? 2 : 4);
    setAmount(calc);
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setError("Please enter a valid transfer amount.");
      return;
    }
    if (numAmount > activeAssetBal) {
      setError(`Insufficient available ${selectedAsset} balance in ${currentSrcWallet?.name || fromWallet}. Available: ${activeAssetBal}`);
      return;
    }
    if (fromWallet === toWallet) {
      setError("Source and destination wallets must be different.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.executeInternalTransfer({
        from_wallet: fromWallet,
        to_wallet: toWallet,
        asset: selectedAsset,
        amount: numAmount,
      });

      if (res.success) {
        setSuccess(res);
        setAmount("");
        onRefresh();
      } else {
        setError(res.error || "Transfer failed. Please check wallet balances.");
      }
    } catch (err: any) {
      setError(err?.message || "Network error executing internal transfer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-[#0F172A] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0B1120]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-500 to-indigo-600 p-[1.5px] shadow-sm">
              <div className="w-full h-full bg-[#090D16] rounded-[10px] flex items-center justify-center">
                <ArrowRightLeft className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
                <span>Binance Internal Transfer</span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  0.00% FEE
                </span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Instant cross-wallet settlement across Binance accounts
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1 text-sm">
          {error && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Transfer Failed</p>
                <p className="opacity-90">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold">Transfer Confirmed (0 Fees)</p>
                <p className="opacity-90">{success.message}</p>
                <div className="font-mono text-[10px] text-slate-400 pt-1">
                  TX: <span className="text-cyan-300">{success.transfer?.tx_hash}</span>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleTransfer} className="space-y-4">
            {/* Wallet Selection Matrix */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
              {/* From Wallet */}
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1 uppercase font-semibold">
                  From Wallet
                </label>
                <select
                  value={fromWallet}
                  onChange={(e) => {
                    setFromWallet(e.target.value);
                    setError(null);
                  }}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-400 transition-colors"
                >
                  {WALLET_OPTIONS.map((opt) => (
                    <option key={opt.id} value={opt.id} disabled={opt.id === toWallet}>
                      {opt.name} ({opt.id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Swap Button */}
              <div className="flex justify-center -my-1">
                <button
                  type="button"
                  onClick={handleSwap}
                  className="p-2 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-400 hover:text-cyan-300 transition-all shadow-md active:scale-95"
                  title="Swap source and destination wallets"
                >
                  <ArrowRightLeft className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* To Wallet */}
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1 uppercase font-semibold">
                  To Wallet
                </label>
                <select
                  value={toWallet}
                  onChange={(e) => {
                    setToWallet(e.target.value);
                    setError(null);
                  }}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-400 transition-colors"
                >
                  {WALLET_OPTIONS.map((opt) => (
                    <option key={opt.id} value={opt.id} disabled={opt.id === fromWallet}>
                      {opt.name} ({opt.id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Asset Selection */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-mono text-slate-300 font-semibold">
                  Select Coin / Asset
                </label>
                <span className="text-[11px] font-mono text-slate-400">
                  Available: <strong className="text-emerald-400">{activeAssetBal} {selectedAsset}</strong>
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {["USDT", "BTC", "ETH", "SOL", "USDC", "BNB", "FDUSD"].map((ast) => (
                  <button
                    key={ast}
                    type="button"
                    onClick={() => setSelectedAsset(ast)}
                    className={`py-2 px-2.5 rounded-xl text-xs font-mono font-bold transition-all border ${
                      selectedAsset === ast
                        ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300 shadow-sm shadow-cyan-500/10"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    {ast}
                  </button>
                ))}
              </div>
            </div>

            {/* Amount Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-mono text-slate-300 font-semibold">
                  Transfer Amount
                </label>
                <div className="flex items-center gap-1">
                  {[0.25, 0.5, 0.75, 1.0].map((pct) => (
                    <button
                      key={pct}
                      type="button"
                      onClick={() => handleQuickPct(pct)}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                    >
                      {pct === 1.0 ? "MAX" : `${pct * 100}%`}
                    </button>
                  ))}
                </div>
              </div>

              <div className="relative">
                <input
                  type="number"
                  step="any"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-white font-mono text-sm focus:outline-none focus:border-cyan-400 transition-colors pr-16"
                />
                <span className="absolute right-3.5 top-2.5 font-mono text-xs font-bold text-slate-400">
                  {selectedAsset}
                </span>
              </div>
            </div>

            {/* Transfer Summary Pill */}
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono space-y-1 text-slate-400">
              <div className="flex justify-between">
                <span>Transfer Type:</span>
                <span className="text-white">Binance Internal (Instant)</span>
              </div>
              <div className="flex justify-between">
                <span>Fee:</span>
                <span className="text-emerald-400 font-bold">0.00 {selectedAsset} (Free)</span>
              </div>
              <div className="flex justify-between">
                <span>Estimated Arrival:</span>
                <span className="text-cyan-300">Immediate (&lt; 100ms)</span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !amount || parseFloat(amount) <= 0}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Processing Internal Transfer...</span>
                </>
              ) : (
                <>
                  <ArrowRightLeft className="w-4 h-4" />
                  <span>Confirm Zero-Fee Transfer</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
