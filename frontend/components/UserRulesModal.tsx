import React, { useState } from "react";
import { Lock, Shield, Check, X } from "lucide-react";
import { UserRules } from "@/types";

interface UserRulesModalProps {
  isOpen: boolean;
  onClose: () => void;
  userRules: UserRules;
  onSaveRules: (updated: Partial<UserRules>) => void;
}

export const UserRulesModal: React.FC<UserRulesModalProps> = ({
  isOpen,
  onClose,
  userRules,
  onSaveRules,
}) => {
  const [capital, setCapital] = useState(userRules.capital_usd);
  const [maxRiskPct, setMaxRiskPct] = useState(userRules.max_risk_pct);
  const [maxLeverage, setMaxLeverage] = useState(userRules.max_leverage);
  const [maxOrderSize, setMaxOrderSize] = useState(userRules.max_order_size_usd);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveRules({
      capital_usd: capital,
      max_risk_pct: maxRiskPct,
      max_leverage: maxLeverage,
      max_order_size_usd: maxOrderSize,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-2xl bg-[#0C1222] border border-indigo-500/40 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Custom Trading Mandate & Risk Rules</h3>
              <p className="text-xs text-slate-400">Mathematical boundaries enforced across all AI decisions.</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          {/* Capital */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Sub-Wallet Allocated Capital ($)
            </label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono outline-none focus:border-indigo-500"
            />
          </div>

          {/* Max Risk % */}
          <div>
            <div className="flex justify-between text-slate-300 font-semibold mb-1">
              <span>Max Loss per Trade (%)</span>
              <span className="text-rose-400 font-mono font-bold">
                {maxRiskPct}% (${((capital * maxRiskPct) / 100).toFixed(2)})
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="5.0"
              step="0.5"
              value={maxRiskPct}
              onChange={(e) => setMaxRiskPct(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
          </div>

          {/* Max Leverage */}
          <div>
            <div className="flex justify-between text-slate-300 font-semibold mb-1">
              <span>Futures Leverage Ceiling</span>
              <span className="text-amber-400 font-mono font-bold">{maxLeverage}x Isolated</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={maxLeverage}
              onChange={(e) => setMaxLeverage(parseInt(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
          </div>

          {/* Max Order Size */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Max Single Order Margin ($)
            </label>
            <input
              type="number"
              value={maxOrderSize}
              onChange={(e) => setMaxOrderSize(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-sm"
          >
            Save Mandate
          </button>
        </div>
      </div>
    </div>
  );
};
