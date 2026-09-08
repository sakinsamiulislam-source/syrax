import React, { useState } from "react";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Percent,
  Layers,
  Scale
} from "lucide-react";
import { DeepReasoningData, Opportunity } from "@/types";

interface StructuredReasoningViewProps {
  reasoning: DeepReasoningData;
  marketData?: Opportunity;
  targetAsset?: string;
  invalidation?: string | null;
}

export const StructuredReasoningView: React.FC<StructuredReasoningViewProps> = ({
  reasoning,
  marketData,
  targetAsset = "ASSET",
  invalidation: propInvalidation,
}) => {
  const [showFullEvidence, setShowFullEvidence] = useState(false);

  const supporting = reasoning.supporting_evidence || reasoning.bull_case || [];
  const contradicting = reasoning.contradicting_evidence || reasoning.bear_case || [];
  const risks = reasoning.key_risks || [];
  const invalidation = propInvalidation || reasoning.invalidation;
  const confidence = reasoning.confidence ?? (marketData?.ai_score || 85);
  const decision = reasoning.decision || marketData?.decision || "ANALYSIS";
  const tradeability = reasoning.tradeability || marketData?.label || "WATCH";

  const getDecisionTheme = () => {
    switch (decision) {
      case "TRADE":
        return {
          badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          border: "border-emerald-500/30",
          label: "TRADE APPROVED (MANDATE COMPLIANT)",
        };
      case "WAIT":
        return {
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          border: "border-amber-500/30",
          label: "WAIT (AWAITING CONFIRMATION)",
        };
      case "PROTECT":
        return {
          badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          border: "border-rose-500/30",
          label: "PROTECT (CAPITAL DEFENSE)",
        };
      default:
        return {
          badge: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
          border: "border-indigo-500/30",
          label: decision || "COGNITIVE SYNTHESIS",
        };
    }
  };

  const theme = getDecisionTheme();

  return (
    <div className={`rounded-xl bg-[#080D18] border ${theme.border} p-4 space-y-3.5 text-slate-200 transition-all shadow-lg`}>
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-wide font-mono">
                DEEP AI REASONING MATRIX
              </span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {reasoning.market_view || targetAsset}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-black bg-amber-500/15 text-amber-400 border border-amber-500/40 flex items-center gap-1 shadow-sm" title="Do Your Own Research">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            DYOR
          </span>
          <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold font-mono border ${theme.badge}`}>
            {theme.label}
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-indigo-300 border border-slate-700">
            {confidence}% Conviction
          </span>
        </div>
      </div>

      {/* Central Thesis */}
      {reasoning.thesis && (
        <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider block">
            Core Analytical Thesis
          </span>
          <p className="text-xs text-slate-200 mt-1 leading-relaxed font-medium">
            {reasoning.thesis}
          </p>
        </div>
      )}

      {/* Bull Case vs Bear Case Dual Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Supporting Evidence / Bull Case */}
        <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 space-y-2">
          <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-bold font-mono uppercase">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Supporting Factors (Bull Case)</span>
          </div>
          {supporting.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-300">
              {supporting.map((point, idx) => (
                <li key={idx} className="flex items-start gap-1.5 leading-snug">
                  <span className="text-emerald-400 mt-0.5 shrink-0">&#8226;</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic">No strong bullish indicators detected.</p>
          )}
        </div>

        {/* Contradicting Evidence / Bear Case */}
        <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 space-y-2">
          <div className="flex items-center gap-1.5 text-rose-400 text-xs font-bold font-mono uppercase">
            <TrendingDown className="w-3.5 h-3.5" />
            <span>Contradicting Factors (Bear Case)</span>
          </div>
          {contradicting.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-300">
              {contradicting.map((point, idx) => (
                <li key={idx} className="flex items-start gap-1.5 leading-snug">
                  <span className="text-rose-400 mt-0.5 shrink-0">&#8226;</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic">No active structural headwinds flagged.</p>
          )}
        </div>
      </div>

      {/* Key Risks & Invalidation Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        {/* Key Risks */}
        {risks.length > 0 && (
          <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-amber-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Key Headwinds & Risk Factors
            </span>
            <ul className="mt-1 space-y-1 text-[11px] text-slate-300">
              {risks.map((risk, idx) => (
                <li key={idx} className="flex items-start gap-1 leading-tight">
                  <span className="text-amber-400 shrink-0">&#8226;</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Explicit Invalidation Trigger */}
        {invalidation && (
          <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-rose-400 flex items-center gap-1">
              <Shield className="w-3 h-3" />
              Mandate Invalidation Level
            </span>
            <p className="mt-1 text-[11px] text-slate-300 leading-relaxed font-mono">
              {invalidation}
            </p>
          </div>
        )}
      </div>

      {/* Grounded Telemetry Strip */}
      {marketData && (
        <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-slate-400">
          <div>
            Spread: <strong className="text-white">{marketData.spread_bps ?? 0.05} bps</strong> | 24h Vol:{" "}
            <strong className="text-white">
              ${((marketData.quote_volume_24h || 50000000) / 1e6).toFixed(1)}M
            </strong>
          </div>
          <div>
            Structure: <strong className="text-indigo-300">{marketData.trend || "CONSOLIDATION"}</strong> | Quality:{" "}
            <strong className="text-emerald-400">{marketData.liquidity_quality || "HIGH"}</strong>
          </div>
        </div>
      )}
    </div>
  );
};
