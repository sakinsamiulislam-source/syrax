import React from "react";
import { AlertTriangle, ShieldCheck, ShieldAlert, Zap, Radio, RefreshCw } from "lucide-react";
import { SentryEvent } from "@/types";

interface SentryRadarViewProps {
  events: SentryEvent[];
  onTriggerProtect: (token: string) => void;
  onSimulateThreat: () => void;
  loading: boolean;
}

export const SentryRadarView: React.FC<SentryRadarViewProps> = ({
  events,
  onTriggerProtect,
  onSimulateThreat,
  loading,
}) => {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>24/7 Sentry Threat & Exploit Radar</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              RADAR ACTIVE
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time surveillance across crypto protocols, bridge RPCs, and smart contract exploit vectors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onSimulateThreat}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-800 transition-colors"
          >
            <Radio className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span>Inject Test Threat</span>
          </button>
        </div>
      </div>

      {/* Events Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {events.map((evt) => {
          const isCritical = evt.severity === "CRITICAL" || evt.severity === "HIGH";

          return (
            <div
              key={evt.id}
              className={`p-4 rounded-xl border transition-all ${
                isCritical
                  ? "bg-rose-950/20 border-rose-500/40 shadow-lg shadow-rose-950/20"
                  : "bg-[#0A0F1D] border-slate-800"
              } space-y-2.5`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white font-mono text-sm">{evt.token}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      isCritical
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}
                  >
                    {evt.severity} SEVERITY
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">{evt.id}</span>
              </div>

              <h4 className="text-xs font-bold text-slate-200">{evt.title}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{evt.summary}</p>

              <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 text-[11px] text-slate-300">
                <span className="font-semibold text-amber-400">Agent Rationale: </span>
                {evt.reasoning}
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span className="truncate max-w-[180px]">{evt.source}</span>
                {isCritical ? (
                  <button
                    onClick={() => onTriggerProtect(evt.token)}
                    className="px-3 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold transition-colors"
                  >
                    Hedge {evt.token} to USDT
                  </button>
                ) : (
                  <span className="text-emerald-400 font-semibold">{evt.action_recommended}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
