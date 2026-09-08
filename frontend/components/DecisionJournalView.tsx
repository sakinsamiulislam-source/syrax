import React from "react";
import { BookOpen, ShieldCheck, AlertCircle } from "lucide-react";
import { JournalEntry } from "@/types";

interface DecisionJournalViewProps {
  journal: JournalEntry[];
}

export const DecisionJournalView: React.FC<DecisionJournalViewProps> = ({ journal }) => {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-indigo-400" />
          <span>Cognitive Decision Journal & Audit Log</span>
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Historical log of every autonomous agentic decision, risk invariant, and rationale.
        </p>
      </div>

      {journal.length === 0 ? (
        <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-1">
          <BookOpen className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">Journal is empty</p>
          <p className="text-xs text-slate-500">
            Mandate evaluations and trade decisions will be logged here automatically.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-[#0A0F1D] overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-medium">
                <tr>
                  <th className="p-3.5">Timestamp & ID</th>
                  <th className="p-3.5">Asset</th>
                  <th className="p-3.5">Decision</th>
                  <th className="p-3.5">Cognitive Rationale</th>
                  <th className="p-3.5">Risk Capped</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Route</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {journal.map((item) => {
                  const isTrade = item.decision === "TRADE";
                  const isProtect = item.decision === "PROTECT";

                  return (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3.5">
                        <div className="font-mono font-bold text-white">{item.id}</div>
                        <div className="text-[10px] text-slate-500">{item.timestamp}</div>
                      </td>

                      <td className="p-3.5 font-bold font-mono text-white">{item.asset}</td>

                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isTrade
                              ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                              : isProtect
                              ? "bg-rose-500/15 text-rose-300 border border-rose-500/30"
                              : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                          }`}
                        >
                          {item.decision}
                        </span>
                      </td>

                      <td className="p-3.5 text-slate-300 max-w-xs">{item.reason}</td>

                      <td className="p-3.5 font-mono text-rose-400 font-semibold">
                        ${item.risk_amount_usd.toFixed(2)} ({item.risk_pct}%)
                      </td>

                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                          {item.status}
                        </span>
                      </td>

                      <td className="p-3.5 text-right text-slate-400 font-mono text-[11px]">{item.route}</td>
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
