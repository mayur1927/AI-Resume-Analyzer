"use client";

import React from "react";
import { RefreshCw, ShieldCheck, CheckCircle2, Cpu } from "lucide-react";

interface OptimizationLoadingProps {
  targetMin: number;
  targetMax: number;
}

const PIPELINE_STAGES = [
  { id: 1, name: "Extracting resume evidence", desc: "Parsing candidate competencies and factual claims" },
  { id: 2, name: "Analyzing job requirements", desc: "Classifying supported vs unsupported competencies" },
  { id: 3, name: "Applying safe transformations", desc: "Standardizing terminology & structuring ATS headers" },
  { id: 4, name: "Re-scoring the resume", desc: "Running deterministic multi-iteration scoring checks" },
  { id: 5, name: "Selecting best safe result", desc: "Enforcing strict non-fabrication guarantee boundary" },
];

export const OptimizationLoading: React.FC<OptimizationLoadingProps> = ({
  targetMin,
  targetMax,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 sm:p-10 shadow-xl text-center space-y-6 max-w-xl mx-auto my-6 animate-in fade-in zoom-in-95 duration-200">
      <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
        <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20 border-t-emerald-500 animate-spin" />
        <RefreshCw className="w-6 h-6 text-emerald-400" />
      </div>

      <div>
        <h3 className="text-lg font-bold text-white">Optimizing Resume</h3>
        <p className="text-xs text-slate-400 mt-1">
          Targeting ATS Score Window: <span className="font-bold text-emerald-400 font-mono">{targetMin}% – {targetMax}%</span>
        </p>
      </div>

      <div className="space-y-2.5 text-left bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span>Active Optimization Pipeline Stages</span>
        </div>
        {PIPELINE_STAGES.map((stage) => (
          <div
            key={stage.id}
            className="flex items-start gap-3 text-xs p-2 rounded-lg bg-slate-900/40 border border-slate-800/50"
          >
            <span className="w-5 h-5 rounded bg-emerald-950/80 border border-emerald-800/60 text-emerald-400 font-mono font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
              {stage.id}
            </span>
            <div>
              <span className="font-semibold text-slate-200 block">{stage.name}</span>
              <span className="text-[11px] text-slate-400">{stage.desc}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 text-[11px] text-slate-400 bg-slate-950/40 py-2 px-3 rounded-lg border border-slate-800/50">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        <span>Non-fabrication guarantee active: Zero unevidenced qualifications are added.</span>
      </div>
    </div>
  );
};