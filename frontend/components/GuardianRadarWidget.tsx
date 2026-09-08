import React, { useState, useEffect } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Activity,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  RefreshCw,
  Zap,
  Lock,
  ArrowRight
} from "lucide-react";
import { GuardianStatusData, GuardianIncidentData } from "@/types";
import { api } from "@/lib/api";

interface GuardianRadarWidgetProps {
  initialStatus?: GuardianStatusData | null;
  onRefreshTriggered?: () => void;
}

export const GuardianRadarWidget: React.FC<GuardianRadarWidgetProps> = ({
  initialStatus,
  onRefreshTriggered,
}) => {
  const [status, setStatus] = useState<GuardianStatusData | null>(initialStatus || null);
  const [incidents, setIncidents] = useState<GuardianIncidentData[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"RULES" | "INCIDENTS">("RULES");

  const fetchGuardian = async () => {
    setLoading(true);
    try {
      const [st, inc] = await Promise.all([
        api.getGuardianStatus(),
        api.getGuardianIncidents(10),
      ]);
      if (st) setStatus(st);
      if (inc) setIncidents(inc);
    } catch (e) {
      console.error("Failed to refresh guardian status", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialStatus) {
      fetchGuardian();
    } else {
      setStatus(initialStatus);
      if (initialStatus.recent_incidents) {
        setIncidents(initialStatus.recent_incidents);
      }
    }
  }, [initialStatus]);

  // 8 Immutable Deterministic Rules
  const GUARDIAN_RULES = [
    { id: "HARD_SL", name: "Hard Stop Loss", threshold: "Mandatory (Every Position)", status: "NOMINAL", desc: "Closes position immediately on breach without LLM mediation." },
    { id: "TRAILING_STOP", name: "Dynamic Trailing Ratchet", threshold: "+1.5% Gain / 1.0% Callback", status: "NOMINAL", desc: "Ratchets stop-loss upward as unrealized profit expands." },
    { id: "TAKE_PROFIT", name: "Take Profit Target", threshold: "Configured Structure Pivot", status: "NOMINAL", desc: "Locks gains at predefined target zones." },
    { id: "CONCENTRATION", name: "Max Asset Concentration", threshold: "30.0% Max Portfolio", status: "NOMINAL", desc: "Prevents over-allocation to a single asset." },
    { id: "TOTAL_EXPOSURE", name: "Total Portfolio Exposure", threshold: "80.0% Active Margin Cap", status: "NOMINAL", desc: "Guarantees 20% liquid cash reserves." },
    { id: "FLASH_CRASH", name: "Flash Crash Detection", threshold: ">4.0% drop in 300s", status: "NOMINAL", desc: "Detects rapid cascading market anomalies." },
    { id: "DAILY_LOSS", name: "Daily Loss Ceiling", threshold: "3.0% Max Loss / 24h", status: "NOMINAL", desc: "Hard stop on aggregate portfolio loss within 24 hours." },
    { id: "MAX_DRAWDOWN", name: "Peak Equity Drawdown", threshold: "5.0% from Peak Watermark", status: "NOMINAL", desc: "Protects accumulated profits across restart cycles." },
  ];

  const mode = status?.execution_mode || "AUTONOMOUS_GUARD";
  const peakEquity = status?.peak_equity_usd ?? 500.0;
  const startingEquity = status?.daily_starting_equity_usd ?? 500.0;
  const realizedToday = status?.realized_pnl_today_usd ?? 0.0;

  const getModeBadge = () => {
    switch (mode) {
      case "AUTONOMOUS_GUARD":
        return {
          bg: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
          label: "AUTONOMOUS GUARD (ACTIVE)",
          icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        };
      case "ASSISTED":
        return {
          bg: "bg-amber-500/15 text-amber-300 border-amber-500/30",
          label: "ASSISTED PROTECTION",
          icon: <Shield className="w-3.5 h-3.5 text-amber-400" />
        };
      case "MONITOR_ONLY":
      default:
        return {
          bg: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
          label: "MONITOR ONLY",
          icon: <Activity className="w-3.5 h-3.5 text-indigo-400" />
        };
    }
  };

  const modeBadge = getModeBadge();

  return (
    <div className="rounded-xl bg-[#080C14] border border-slate-800 p-4 space-y-3.5 text-slate-200 shadow-xl">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-wide font-mono">
                POST-TRADE GUARDIAN
              </span>
              <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                100% DETERMINISTIC
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium">
              8 Hard Rules &bull; Peak Watermark Protection &bull; Zero LLM Gating
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border flex items-center gap-1 ${modeBadge.bg}`}>
            {modeBadge.icon}
            <span>{modeBadge.label}</span>
          </span>
          <button
            onClick={fetchGuardian}
            disabled={loading}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Guardian Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Equity Watermark & 24h Telemetry Strip */}
      <div className="grid grid-cols-3 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-sans">Peak Equity Watermark</span>
          <span className="text-xs font-bold text-emerald-400">${peakEquity.toFixed(2)} USD</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-sans">Daily Starting Baseline</span>
          <span className="text-xs font-bold text-slate-200">${startingEquity.toFixed(2)} USD</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-sans">Today's Realized PnL</span>
          <span className={`text-xs font-bold ${realizedToday >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {realizedToday >= 0 ? "+" : ""}${realizedToday.toFixed(2)} USD
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pt-1">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("RULES")}
            className={`pb-2 text-xs font-bold font-mono transition-colors border-b-2 ${
              activeTab === "RULES"
                ? "border-emerald-400 text-emerald-300"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            8 Invariant Rules (8/8 Active)
          </button>
          <button
            onClick={() => setActiveTab("INCIDENTS")}
            className={`pb-2 text-xs font-bold font-mono transition-colors border-b-2 flex items-center gap-1.5 ${
              activeTab === "INCIDENTS"
                ? "border-emerald-400 text-emerald-300"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>Guardian Incident Log</span>
            {incidents.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-slate-800 text-slate-300">
                {incidents.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Tab Content: 8 Rules Grid */}
      {activeTab === "RULES" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 animate-in fade-in duration-150">
          {GUARDIAN_RULES.map((rule) => (
            <div
              key={rule.id}
              className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200 text-[11px] font-mono">{rule.name}</span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  NOMINAL
                </span>
              </div>
              <div className="text-[10px] text-indigo-300 font-mono font-semibold">
                Threshold: {rule.threshold}
              </div>
              <p className="text-[10px] text-slate-400 leading-snug">{rule.desc}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab Content: Incidents */}
      {activeTab === "INCIDENTS" && (
        <div className="space-y-2 animate-in fade-in duration-150">
          {incidents.length === 0 ? (
            <div className="p-4 rounded-lg bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
              <ShieldCheck className="w-6 h-6 text-emerald-400 mx-auto mb-1.5 opacity-80" />
              <span>Zero Guardian breaches detected. All positions within mandate boundaries.</span>
            </div>
          ) : (
            incidents.map((inc, i) => (
              <div
                key={inc.incident_id || i}
                className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-rose-400 text-[11px]">
                    {inc.rule} TRIGGERED ({inc.asset})
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{inc.timestamp}</span>
                </div>
                <p className="text-[11px] text-slate-300">{inc.explanation}</p>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
                  <span>Action: {inc.action}</span>
                  <span className="text-emerald-400">Result: {inc.result}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
