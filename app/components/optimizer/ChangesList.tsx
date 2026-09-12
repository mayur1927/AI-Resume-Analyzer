"use client";

import React, { useState } from "react";
import { ChangeRecord, OptimizationIteration } from "@/app/types/optimizer";
import { Check, ArrowRight, ShieldCheck, ChevronDown, ChevronUp, Layers, ListChecks } from "lucide-react";

interface ChangesListProps {
  changes?: ChangeRecord[];
  iterations?: OptimizationIteration[];
}

export const ChangesList: React.FC<ChangesListProps> = ({ changes = [], iterations = [] }) => {
  const [showIterationLog, setShowIterationLog] = useState(false);

  const getChangeTypeBadge = (type: string) => {
    switch (type) {
      case "skills_reordered":
        return { label: "Reordered", bg: "bg-blue-950/80 border-blue-700 text-blue-300" };
      case "alias_normalized":
        return { label: "Standardized", bg: "bg-cyan-950/80 border-cyan-700 text-cyan-300" };
      case "summary_targeted":
        return { label: "Targeted Summary", bg: "bg-emerald-950/80 border-emerald-700 text-emerald-300" };
      case "bullet_clarified":
        return { label: "Action Verb", bg: "bg-purple-950/80 border-purple-700 text-purple-300" };
      case "section_header_normalized":
        return { label: "ATS Header", bg: "bg-amber-950/80 border-amber-700 text-amber-300" };
      default:
        return { label: type, bg: "bg-slate-800 border-slate-700 text-slate-300" };
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header with Iteration Log Toggle */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-white flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-emerald-400" />
            <span>Audit Trail: {changes.length} Applied Safe Changes</span>
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Every modification is strictly derived from your original resume text and factual evidence.
          </p>
        </div>

        {iterations && iterations.length > 0 && (
          <button
            type="button"
            onClick={() => setShowIterationLog(!showIterationLog)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span>{showIterationLog ? "Hide" : "View"} Iteration Loop ({iterations.length})</span>
            {showIterationLog ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      {/* Iteration Diagnostics Log (Collapsible) */}
      {showIterationLog && iterations && iterations.length > 0 && (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3 animate-in fade-in duration-200">
          <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Optimizer Iteration Step Log
          </h5>
          <div className="space-y-2">
            {iterations.map((iter, idx) => {
              const iterNum = iter.iteration_number ?? iter.iteration ?? (idx + 1);
              const scoreVal = iter.ats_score ?? iter.score_after ?? 0;
              const opName = iter.applied_operation ?? iter.summary ?? "Score Evaluated";

              return (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-md bg-slate-800 font-bold flex items-center justify-center text-slate-300 font-mono text-[11px]">
                      #{iterNum}
                    </span>
                    <div>
                      <span className="font-semibold text-slate-200 block">
                        {opName}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        Score After Step: <strong className="text-emerald-400">{Math.round(scoreVal)}%</strong>
                        {iter.score_delta !== undefined && iter.score_delta > 0 && (
                          <span className="text-emerald-400 ml-1">
                            (+{Math.round(iter.score_delta)}%)
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    {iter.target_met ? (
                      <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                        Target Met
                      </span>
                    ) : (
                      <span className="text-[10px] font-medium text-slate-400">
                        Step Complete
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Changes List Cards */}
      {changes && changes.length > 0 ? (
        <div className="space-y-3">
          {changes.map((change, idx) => {
            const badge = getChangeTypeBadge(change.change_type);
            const evidence = change.evidence_used || change.evidence || "Direct resume evidence";

            return (
              <div
                key={idx}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 transition-all hover:border-slate-700"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${badge.bg}`}>
                      {badge.label}
                    </span>
                    <span className="text-xs font-bold text-slate-200">
                      Section: {change.section}
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-400 font-medium">
                    {change.reason}
                  </span>
                </div>

                {/* Diff Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  {/* Original */}
                  <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400">
                      Original Text
                    </span>
                    <p className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                      {change.original_text || "(empty / absent)"}
                    </p>
                  </div>

                  {/* Optimized */}
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/40 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                      Optimized Text
                    </span>
                    <p className="text-xs text-emerald-200 font-mono whitespace-pre-wrap leading-relaxed">
                      {change.optimized_text}
                    </p>
                  </div>
                </div>

                {/* Evidence Used Disclosure */}
                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Evidence used: <strong className="text-slate-300">{evidence}</strong></span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-10 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-400">
          No modifications were required; the resume was already well-aligned with job description evidence.
        </div>
      )}
    </div>
  );
};