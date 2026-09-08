import React from "react";
import { Shield, Radio, Copy, RefreshCw, Lock, Terminal, Play, Pause, Activity, ShieldCheck, Layers, Server, ArrowRightLeft } from "lucide-react";
import { MonitorStatus, MCPInfo, Portfolio, SubWalletData, GuardianStatusData, BinanceMCPStatus } from "@/types";
import { AnimatedNumber } from "./AnimatedNumber";

import { SyraxLogo } from "./SyraxLogo";

interface HeaderProps {
  loading: boolean;
  onRefresh: () => void;
  monitorStatus: MonitorStatus | null;
  onToggleMonitor: () => void;
  mcpInfo: MCPInfo | null;
  onCopyMcpUrl: () => void;
  isWsLive: boolean;
  tickerCount: number;
  portfolio: Portfolio | null;
  subWalletData: SubWalletData | null;
  guardianStatus?: GuardianStatusData | null;
  binanceMcpStatus?: BinanceMCPStatus | null;
  onOpenRules: () => void;
  onOpenBinanceMcp: () => void;
  activeMandateRiskPct: number;
  onOpenTransfer?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  loading,
  onRefresh,
  monitorStatus,
  onToggleMonitor,
  onCopyMcpUrl,
  isWsLive,
  tickerCount,
  portfolio,
  subWalletData,
  guardianStatus,
  binanceMcpStatus,
  onOpenRules,
  onOpenBinanceMcp,
  activeMandateRiskPct,
  onOpenTransfer,
}) => {
  const isSentinelPaused = monitorStatus?.is_paused ?? false;
  const availableCash = subWalletData?.analysis?.available_cash_usd ?? portfolio?.available_cash_usd ?? 250.0;
  const totalValue = subWalletData?.analysis?.total_portfolio_value_usd ?? portfolio?.total_value_usd ?? 500.0;
  const isMcpLive = binanceMcpStatus?.is_connected ?? false;

  return (
    <header className="border-b border-slate-800/80 bg-[#0B1120]/95 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-[68px] flex items-center justify-between gap-4">
        {/* Logo & Product Identity: SYRAX */}
        <SyraxLogo />

        {/* Center Live Agentic Beacons (Desktop/Tablet) */}
        <div className="hidden md:flex items-center gap-2.5 text-xs">
          {/* Environment Indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 font-mono text-[11px]">
            <Server className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">ENV:</span>
            <span className={`font-bold ${isMcpLive ? "text-amber-400" : "text-emerald-400"}`}>
              {isMcpLive ? "BINANCE AGENT OS" : "SIMULATED / DEMO"}
            </span>
          </div>

          {/* Account Scope */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 font-mono text-[11px]">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">ACCOUNT:</span>
            <span className="font-bold text-white">
              {isMcpLive ? (binanceMcpStatus?.sub_account_id || "AGENTIC-SUB") : "AGENTIC SUB-ACCOUNT"}
            </span>
            <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold ${isMcpLive ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-800 text-slate-400"}`}>
              {isMcpLive ? "CONNECTED" : "OFFLINE"}
            </span>
          </div>

          {/* Sub-Wallet Execution Quarantine */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span className="text-slate-400">Cash:</span>
            <AnimatedNumber
              value={availableCash}
              prefix="$"
              className="font-mono font-bold text-white"
            />
            <span className="text-[10px] text-slate-500">
              / ${totalValue.toFixed(2)}
            </span>
          </div>

          {/* Guardian Status Indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-mono text-[11px] font-semibold">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>GUARDIAN: 8/8 ARMED</span>
          </div>
        </div>

        {/* Right Quick Controls */}
        <div className="flex items-center gap-2.5">
          {/* Always Visible Binance MCP Connect Trigger */}
          <button
            onClick={onOpenBinanceMcp}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl font-mono text-xs font-bold transition-all shadow-md active:scale-95 ${
              isMcpLive
                ? "bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/30 shadow-emerald-500/20"
                : "bg-amber-500 hover:bg-amber-400 text-black border border-amber-400 shadow-amber-500/30 font-extrabold"
            }`}
            title="Connect / Inspect Binance Agent OS MCP Account"
          >
            <span className="text-sm">🔶</span>
            <span>{isMcpLive ? "● MCP CONNECTED" : "CONNECT BINANCE MCP"}</span>
          </button>

          {onOpenTransfer && (
            <button
              onClick={onOpenTransfer}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-semibold transition-all active:scale-95"
              title="Binance Internal Cross-Wallet Transfer (0% Fee)"
            >
              <ArrowRightLeft className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden sm:inline">Transfer</span>
            </button>
          )}

          <button
            onClick={onOpenRules}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold transition-all active:scale-95"
          >
            <Lock className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Mandate</span>
            <span className="text-[10px] font-mono font-bold bg-indigo-500/20 px-1.5 py-0.2 rounded">
              {activeMandateRiskPct}% Loss Cap
            </span>
          </button>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-all active:scale-95"
            title="Refresh live telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
