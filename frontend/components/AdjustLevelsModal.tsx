import React, { useState, useEffect } from "react";
import { Sliders, X } from "lucide-react";
import { SubWalletTrade } from "@/types";

interface AdjustLevelsModalProps {
  trade: SubWalletTrade | null;
  onClose: () => void;
  onSave: (sl?: number, tp?: number) => void;
  loading: boolean;
}

export const AdjustLevelsModal: React.FC<AdjustLevelsModalProps> = ({
  trade,
  onClose,
  onSave,
  loading,
}) => {
  const [stopLoss, setStopLoss] = useState<string>("");
  const [takeProfit, setTakeProfit] = useState<string>("");

  useEffect(() => {
    if (trade) {
      setStopLoss(trade.stop_loss ? String(trade.stop_loss) : "");
      setTakeProfit(trade.take_profit ? String(trade.take_profit) : "");
    }
  }, [trade]);

  if (!trade) return null;

  const handleSave = () => {
    onSave(
      stopLoss ? parseFloat(stopLoss) : undefined,
      takeProfit ? parseFloat(takeProfit) : undefined
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="rounded-2xl bg-[#0C1222] border border-indigo-500/40 max-w-sm w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <span>Adjust SL / TP: {trade.symbol}</span>
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex justify-between font-mono">
            <span className="text-slate-400">Entry Price:</span>
            <span className="font-bold text-white">${trade.entry_price}</span>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Stop-Loss Price ($)</label>
            <input
              type="number"
              step="any"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              placeholder="e.g. 175.50"
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Take-Profit Price ($)</label>
            <input
              type="number"
              step="any"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              placeholder="e.g. 195.00"
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
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-sm"
          >
            {loading ? "Saving..." : "Save Levels"}
          </button>
        </div>
      </div>
    </div>
  );
};
