"use client";

import React from "react";
import { History, RefreshCw, Clock, ExternalLink, CheckCircle2, Zap } from "lucide-react";
import { OptimizationHistoryItem } from "@/app/types/optimizer";

interface OptimizerHistoryProps {
  historyList: OptimizationHistoryItem[];
  isLoading: boolean;
  onRefresh: () => void;
  onSelect: (optimizationId: string) => void;
  selectedId?: string | null;
}

export const OptimizerHistory: React.FC<OptimizerHistoryProps> = ({
  historyList,
  isLoading,
  onRefresh,
  onSelect,
  selectedId,
}) => {
  const formatTimestamp = (dateStr: string | null | undefined) => {
    if (!dateStr) return "Just now";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <History className="w-4 h-4 text-emerald-400" />
          <span>Recent Optimizations</span>
        </h3>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh optimization history"
          className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-emerald-400" : ""}`} />
        </button>
      </div>

      <div className="flex-1 space-y-2.5 overflow-y-auto max-h-[440px] pr-1">
        {historyList.length > 0 ? (
          historyList.map((item) => {
            const isSelected = selectedId === item.optimization_id;
            const scoreDelta = Math.round(item.final_score - item.original_score);

            return (
              <div
                key={item.optimization_id}
                onClick={() => onSelect(item.optimization_id)}
                className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                  isSelected
                    ? "bg-emerald-950/40 border-emerald-500/60 shadow-sm"
                    : "bg-slate-950/50 hover:bg-slate-950/90 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-white">
                        {Math.round(item.original_score)}% → {Math.round(item.final_score)}%
                      </span>
                      {scoreDelta > 0 && (
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.2 rounded border border-emerald-800/50">
                          +{scoreDelta}%
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{formatTimestamp(item.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end shrink-0">
                    {item.target_achieved ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-300">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        Target Met
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400">
                        Best Safe
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
                  <span>Target: {item.target_min}%–{item.target_max}%</span>
                  <span className="text-emerald-400 font-medium inline-flex items-center gap-0.5 hover:underline">
                    View Details <ExternalLink className="w-2.5 h-2.5" />
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-8 px-4 text-xs text-slate-500 space-y-1">
            <p>No saved optimizations in this session yet.</p>
            <p className="text-[11px] text-slate-600">Run an optimization to track your history.</p>
          </div>
        )}
      </div>
    </div>
  );
};
