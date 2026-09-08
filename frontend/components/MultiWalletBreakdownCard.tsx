"use client";

import React, { useState } from "react";
import {
  Wallet,
  Coins,
  TrendingUp,
  Zap,
  Layers,
  ArrowRightLeft,
  ChevronRight,
  Shield,
  RefreshCw,
  ExternalLink,
  History,
  CheckCircle2,
  Sliders,
  DollarSign,
  PieChart,
  Eye,
  ArrowUpRight
} from "lucide-react";
import { WalletsSummaryData, WalletItemData } from "@/types";
import { AnimatedNumber } from "./AnimatedNumber";

interface MultiWalletBreakdownCardProps {
  walletsData: WalletsSummaryData | null;
  onOpenTransfer: (from?: string, to?: string) => void;
  onRefresh: () => void;
  loading?: boolean;
}

const WALLET_ICONS: Record<string, any> = {
  SPOT: Wallet,
  FUNDING: Coins,
  USDT_FUTURES: TrendingUp,
  COIN_FUTURES: Zap,
  CROSS_MARGIN: Layers,
};

const WALLET_THEMES: Record<string, { badge: string; border: string; glow: string; text: string; bg: string }> = {
  SPOT: { 
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/30", 
    border: "border-amber-500/40", 
    glow: "hover:border-amber-400", 
    text: "text-amber-400",
    bg: "from-amber-950/20 to-slate-900/40"
  },
  FUNDING: { 
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30", 
    border: "border-emerald-500/40", 
    glow: "hover:border-emerald-400", 
    text: "text-emerald-400",
    bg: "from-emerald-950/20 to-slate-900/40"
  },
  USDT_FUTURES: { 
    badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30", 
    border: "border-cyan-500/40", 
    glow: "hover:border-cyan-400", 
    text: "text-cyan-400",
    bg: "from-cyan-950/20 to-slate-900/40"
  },
  COIN_FUTURES: { 
    badge: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30", 
    border: "border-indigo-500/40", 
    glow: "hover:border-indigo-400", 
    text: "text-indigo-400",
    bg: "from-indigo-950/20 to-slate-900/40"
  },
  CROSS_MARGIN: { 
    badge: "bg-purple-500/10 text-purple-400 border-purple-500/30", 
    border: "border-purple-500/40", 
    glow: "hover:border-purple-400", 
    text: "text-purple-400",
    bg: "from-purple-950/20 to-slate-900/40"
  },
};

export const MultiWalletBreakdownCard: React.FC<MultiWalletBreakdownCardProps> = ({
  walletsData,
  onOpenTransfer,
  onRefresh,
  loading = false,
}) => {
  const [selectedWalletId, setSelectedWalletId] = useState<string>("SPOT");
  const [viewMode, setViewMode] = useState<"WALLET_INSPECTOR" | "ALL_MATRIX" | "TRANSFERS">("WALLET_INSPECTOR");

  const rawWallets = walletsData?.wallets || [
    {
      wallet_id: "SPOT",
      name: "Fiat & Spot",
      badge: "SPOT",
      description: "Spot trading and primary asset vault",
      total_value_usd: 250.0,
      allocation_pct: 50.0,
      asset_count: 4,
      assets: [
        { asset: "USDT", free: 240.0, locked: 0.0, total: 240.0, price_usd: 1.0, value_usd: 240.0 },
        { asset: "BTC", free: 0.0016, locked: 0.0, total: 0.0016, price_usd: 79000.0, value_usd: 126.40 },
        { asset: "ETH", free: 0.028, locked: 0.0, total: 0.028, price_usd: 2500.0, value_usd: 70.00 },
        { asset: "SOL", free: 0.2, locked: 0.0, total: 0.2, price_usd: 105.0, value_usd: 21.00 },
        { asset: "USDC", free: 12.5, locked: 0.0, total: 12.5, price_usd: 1.0, value_usd: 12.50 }
      ]
    },
    {
      wallet_id: "FUNDING",
      name: "Funding Wallet",
      badge: "FUNDING",
      description: "P2P trading, Binance Pay, crypto card, and merchant settlements",
      total_value_usd: 135.0,
      allocation_pct: 20.0,
      asset_count: 3,
      assets: [
        { asset: "BNB", free: 0.08, locked: 0.0, total: 0.08, price_usd: 750.0, value_usd: 60.00 },
        { asset: "USDT", free: 50.0, locked: 0.0, total: 50.0, price_usd: 1.0, value_usd: 50.00 },
        { asset: "FDUSD", free: 25.0, locked: 0.0, total: 25.0, price_usd: 1.0, value_usd: 25.00 }
      ]
    },
    {
      wallet_id: "USDT_FUTURES",
      name: "USD(S)-M Futures",
      badge: "USD-M",
      description: "Perpetual & delivery contracts with USDT/USDC collateral",
      total_value_usd: 57.89,
      allocation_pct: 10.0,
      asset_count: 2,
      assets: [
        { asset: "USDT", free: 40.0, locked: 7.89, total: 47.89, price_usd: 1.0, value_usd: 47.89 },
        { asset: "USDC", free: 10.0, locked: 0.0, total: 10.0, price_usd: 1.0, value_usd: 10.00 }
      ]
    },
    {
      wallet_id: "COIN_FUTURES",
      name: "Coin-M Futures",
      badge: "COIN-M",
      description: "Coin-margined contracts settled directly in underlying crypto",
      total_value_usd: 55.55,
      allocation_pct: 10.0,
      asset_count: 2,
      assets: [
        { asset: "BTC", free: 0.00045, locked: 0.0, total: 0.00045, price_usd: 79000.0, value_usd: 35.55 },
        { asset: "ETH", free: 0.008, locked: 0.0, total: 0.008, price_usd: 2500.0, value_usd: 20.00 }
      ]
    },
    {
      wallet_id: "CROSS_MARGIN",
      name: "Cross Margin (3x/5x)",
      badge: "MARGIN",
      description: "Unified collateral risk pool for leveraged spot margin trading",
      total_value_usd: 45.80,
      allocation_pct: 10.0,
      asset_count: 2,
      assets: [
        { asset: "USDT", free: 30.0, locked: 0.0, total: 30.0, price_usd: 1.0, value_usd: 30.00 },
        { asset: "BTC", free: 0.0002, locked: 0.0, total: 0.0002, price_usd: 79000.0, value_usd: 15.80 }
      ]
    }
  ];

  // Filter out EARN if present in raw backend response
  const wallets = rawWallets.filter((w) => w.wallet_id !== "EARN");
  const totalEcosystemUsd = wallets.reduce((acc, w) => acc + (w.total_value_usd || 0), 0);
  const activeWallet = wallets.find((w) => w.wallet_id === selectedWalletId) || wallets[0];
  const recentTransfers = walletsData?.recent_transfers || [];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-[#080C14] border border-slate-800/90 shadow-2xl space-y-5">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
            <Wallet className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-white tracking-wide font-mono">
                BINANCE MULTI-WALLET &amp; ASSET INSPECTOR
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-bold">
                5 TRADING WALLETS
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
                0.00% TRANSFER FEE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any wallet card below to inspect exact token amounts, locked margin, and execute instant internal transfers.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Navigation View Switcher */}
          <div className="flex items-center bg-slate-900/90 rounded-xl p-1 border border-slate-800">
            <button
              onClick={() => setViewMode("WALLET_INSPECTOR")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all ${
                viewMode === "WALLET_INSPECTOR"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <PieChart className="w-3.5 h-3.5" />
              <span>Wallet Inspector</span>
            </button>
            <button
              onClick={() => setViewMode("ALL_MATRIX")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all ${
                viewMode === "ALL_MATRIX"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>All Tokens Matrix</span>
            </button>
            <button
              onClick={() => setViewMode("TRANSFERS")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all ${
                viewMode === "TRANSFERS"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Transfers ({recentTransfers.length})</span>
            </button>
          </div>

          <button
            onClick={() => onOpenTransfer(selectedWalletId, selectedWalletId === "SPOT" ? "USDT_FUTURES" : "SPOT")}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-blue-500 text-white font-mono text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 transition-all active:scale-95 shrink-0"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            <span>Transfer Funds</span>
          </button>
        </div>
      </div>

      {/* 5 Interactive Wallet Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {wallets.map((w) => {
          const IconComp = WALLET_ICONS[w.wallet_id] || Wallet;
          const theme = WALLET_THEMES[w.wallet_id] || WALLET_THEMES.SPOT;
          const isSelected = w.wallet_id === selectedWalletId;
          const allocPct = totalEcosystemUsd > 0 ? ((w.total_value_usd / totalEcosystemUsd) * 100).toFixed(1) : "0.0";

          return (
            <button
              key={w.wallet_id}
              onClick={() => {
                setSelectedWalletId(w.wallet_id);
                if (viewMode === "TRANSFERS") setViewMode("WALLET_INSPECTOR");
              }}
              className={`p-3.5 rounded-xl text-left transition-all border relative flex flex-col justify-between cursor-pointer ${
                isSelected
                  ? `bg-gradient-to-b ${theme.bg} ${theme.border} shadow-lg ring-2 ring-cyan-400/40 shadow-cyan-500/10`
                  : "bg-slate-950/80 border-slate-800 hover:bg-slate-900/70 " + theme.glow
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`p-1.5 rounded-lg bg-slate-900 border border-slate-800 ${theme.badge}`}>
                  <IconComp className="w-4 h-4" />
                </span>
                <span className="text-[10px] font-mono font-bold text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
                  {allocPct}%
                </span>
              </div>

              <div>
                <span className="text-xs font-bold text-slate-200 block truncate">
                  {w.name}
                </span>
                <AnimatedNumber
                  value={w.total_value_usd}
                  prefix="$"
                  decimals={2}
                  className="text-base font-bold font-mono text-white block mt-0.5"
                />
                <div className="flex items-center justify-between mt-1 text-[10px] font-mono text-slate-400">
                  <span>{w.assets?.length || 0} Assets</span>
                  <span className={isSelected ? "text-cyan-400 font-bold" : "text-slate-500"}>
                    {isSelected ? "Active View" : "Click to view"}
                  </span>
                </div>
              </div>

              {isSelected && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              )}
            </button>
          );
        })}
      </div>

      {/* VIEW 1: ACTIVE WALLET ASSET INSPECTOR DRAWER */}
      {viewMode === "WALLET_INSPECTOR" && activeWallet && (
        <div className="p-5 rounded-xl bg-slate-950/95 border border-slate-800 space-y-4 animate-in fade-in duration-200">
          {/* Drawer Top Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl border ${WALLET_THEMES[activeWallet.wallet_id]?.badge || 'bg-slate-900'}`}>
                {React.createElement(WALLET_ICONS[activeWallet.wallet_id] || Wallet, { className: "w-5 h-5" })}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-white font-mono uppercase">
                    {activeWallet.name} — Live Asset Holdings
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {activeWallet.assets?.length || 0} Coins in Wallet
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  {activeWallet.description}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="bg-slate-900/90 px-3 py-1.5 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-[10px] block uppercase">Total Valuation</span>
                <AnimatedNumber
                  value={activeWallet.total_value_usd}
                  prefix="$"
                  decimals={2}
                  className="text-sm font-bold text-cyan-300"
                />
              </div>
              <button
                onClick={() => onOpenTransfer(activeWallet.wallet_id, activeWallet.wallet_id === "SPOT" ? "USDT_FUTURES" : "SPOT")}
                className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md active:scale-95"
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
                <span>Move Assets from {activeWallet.badge}</span>
              </button>
            </div>
          </div>

          {/* Detailed Token Holdings Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {(activeWallet.assets || []).map((ast) => {
              const tokenShare = activeWallet.total_value_usd > 0
                ? ((ast.value_usd / activeWallet.total_value_usd) * 100).toFixed(1)
                : "0.0";

              return (
                <div
                  key={ast.asset}
                  className="p-4 rounded-xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/90 hover:border-slate-700 transition-all space-y-2.5 shadow-sm"
                >
                  {/* Token Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center font-bold text-xs text-indigo-300 font-mono">
                        {ast.asset.slice(0, 3)}
                      </div>
                      <div>
                        <span className="font-bold font-mono text-sm text-white block">
                          {ast.asset}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          @ ${ast.price_usd?.toLocaleString() ?? 1.0}
                        </span>
                      </div>
                    </div>

                    <div className="text-right">
                      <AnimatedNumber
                        value={ast.value_usd}
                        prefix="$"
                        decimals={2}
                        className="text-sm font-bold font-mono text-white block"
                      />
                      <span className="text-[10px] font-mono text-slate-400 block">
                        {tokenShare}% of wallet
                      </span>
                    </div>
                  </div>

                  {/* Quantity Breakdown (Free vs Locked) */}
                  <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-[11px] font-mono">
                    <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">Free / Available</span>
                      <span className="font-bold text-emerald-400">{ast.free} {ast.asset}</span>
                    </div>

                    <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">Locked in Orders</span>
                      <span className={ast.locked > 0 ? "font-bold text-amber-400" : "text-slate-500"}>
                        {ast.locked} {ast.asset}
                      </span>
                    </div>
                  </div>

                  {/* Action Row */}
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] font-mono text-slate-500">
                      Total: {(ast.total || (ast.free + ast.locked))} {ast.asset}
                    </span>
                    <button
                      onClick={() => onOpenTransfer(activeWallet.wallet_id, activeWallet.wallet_id === "SPOT" ? "USDT_FUTURES" : "SPOT")}
                      className="text-[10px] font-mono font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 hover:underline"
                    >
                      <ArrowRightLeft className="w-3 h-3" />
                      <span>Transfer {ast.asset}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 2: ALL TOKENS CONSOLIDATED MATRIX */}
      {viewMode === "ALL_MATRIX" && (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
            <span className="text-xs font-bold text-white font-mono uppercase flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <span>Consolidated Binance Multi-Wallet Matrix (Where What Tokens Are)</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              Total Ecosystem: ${totalEcosystemUsd.toFixed(2)} USD
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[10px]">
                  <th className="pb-2 font-semibold">TOKEN</th>
                  <th className="pb-2 font-semibold">PRICE</th>
                  <th className="pb-2 font-semibold">LOCATED IN WALLET</th>
                  <th className="pb-2 font-semibold">FREE BALANCE</th>
                  <th className="pb-2 font-semibold">LOCKED MARGIN</th>
                  <th className="pb-2 font-semibold">TOTAL VALUE (USD)</th>
                  <th className="pb-2 font-semibold text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {wallets.flatMap((w) =>
                  (w.assets || []).map((ast) => (
                    <tr key={`${w.wallet_id}-${ast.asset}`} className="hover:bg-slate-900/40">
                      <td className="py-2.5 font-bold text-white flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        <span>{ast.asset}</span>
                      </td>
                      <td className="py-2.5 text-slate-400">${ast.price_usd?.toLocaleString() ?? 1.0}</td>
                      <td className="py-2.5">
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${WALLET_THEMES[w.wallet_id]?.badge || 'bg-slate-900 text-slate-300'}`}>
                          {w.name}
                        </span>
                      </td>
                      <td className="py-2.5 text-emerald-400 font-bold">{ast.free} {ast.asset}</td>
                      <td className="py-2.5 text-slate-400">
                        {ast.locked > 0 ? (
                          <span className="text-amber-400 font-bold">{ast.locked} {ast.asset}</span>
                        ) : (
                          "0.00"
                        )}
                      </td>
                      <td className="py-2.5 font-bold text-white">${ast.value_usd?.toFixed(2)}</td>
                      <td className="py-2.5 text-right">
                        <button
                          onClick={() => onOpenTransfer(w.wallet_id, w.wallet_id === "SPOT" ? "USDT_FUTURES" : "SPOT")}
                          className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[10px] text-cyan-400 font-bold hover:text-white transition-all"
                        >
                          Transfer
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* VIEW 3: TRANSFER AUDIT HISTORY */}
      {viewMode === "TRANSFERS" && (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
            <span className="text-xs font-bold text-white font-mono uppercase flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" />
              <span>Internal Cross-Wallet Transfer Receipts (Zero-Fee)</span>
            </span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 font-bold">
              0.0000 USDT TOTAL FEES
            </span>
          </div>

          {recentTransfers.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs font-mono">
              No internal transfers recorded yet. Click &quot;Transfer Funds&quot; to execute your first instant transfer.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[10px]">
                    <th className="pb-2 font-semibold">TRANSFER ID</th>
                    <th className="pb-2 font-semibold">FROM</th>
                    <th className="pb-2 font-semibold">TO</th>
                    <th className="pb-2 font-semibold">AMOUNT / ASSET</th>
                    <th className="pb-2 font-semibold">FEE</th>
                    <th className="pb-2 font-semibold">STATUS</th>
                    <th className="pb-2 font-semibold">TIMESTAMP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {recentTransfers.map((tx: any) => (
                    <tr key={tx.transfer_id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 font-bold text-indigo-400">{tx.transfer_id}</td>
                      <td className="py-2.5">
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-amber-400 font-bold">
                          {tx.from_wallet}
                        </span>
                      </td>
                      <td className="py-2.5">
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-cyan-400 font-bold">
                          {tx.to_wallet}
                        </span>
                      </td>
                      <td className="py-2.5 font-bold text-white">
                        {tx.amount} {tx.asset}
                      </td>
                      <td className="py-2.5 text-emerald-400 font-bold">
                        0.00 (Free)
                      </td>
                      <td className="py-2.5">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-[10px] text-emerald-400 font-bold">
                          <CheckCircle2 className="w-2.5 h-2.5" />
                          <span>{tx.status || "CONFIRMED"}</span>
                        </span>
                      </td>
                      <td className="py-2.5 text-slate-500 text-[10px]">{tx.timestamp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
