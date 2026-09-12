"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ArrowRight, TrendingUp, ShieldAlert, Cpu } from "lucide-react";
import { OptimizationResult } from "@/app/types/optimizer";

interface ScoreComparisonProps {
  result: OptimizationResult;
}

export const ScoreComparison: React.FC<ScoreComparisonProps> = ({ result }) => {
  const scoreDelta = result.final_score - result.original_score;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-7 shadow-lg space-y-6">
      {/* Top Banner: Status & Target Range */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Optimization Summary
            </span>
            <span className="text-xs text-slate-500">• ID: {result.optimization_id.slice(0, 8)}</span>
          </div>
          <h3 className="text-xl font-extrabold text-white tracking-tight">
            ATS Compatibility Score Progression
          </h3>
        </div>

        <div>
          {result.target_achieved ? (
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-emerald-950/80 border border-emerald-600/80 text-emerald-300 text-xs font-bold shadow-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Target Achieved (✓ YES)</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-amber-950/80 border border-amber-600/80 text-amber-300 text-xs font-bold shadow-sm">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Plateaued at Best Safe Score</span>
            </div>
          )}
        </div>
      </div>

      {/* 3-Card Score Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* 1. Original Score */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-center flex flex-col justify-center">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Original Match Score
          </span>
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-3xl font-extrabold text-slate-300">
              {Math.round(result.original_score)}%
            </span>
          </div>
          <span className="text-[10px] text-slate-500 mt-1">Baseline document</span>
        </div>

        {/* 2. Target Range */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-center flex flex-col justify-center">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Desired ATS Target
          </span>
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-2xl font-extrabold text-emerald-400 font-mono">
              {result.target_min}% – {result.target_max}%
            </span>
          </div>
          <span className="text-[10px] text-slate-500 mt-1">Configured bounds</span>
        </div>

        {/* 3. Final Score */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-center flex flex-col justify-center relative overflow-hidden">
          <div className="absolute top-2 right-2 text-emerald-400">
            {scoreDelta > 0 && (
              <span className="inline-flex items-center text-[11px] font-bold px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40">
                +{Math.round(scoreDelta)}%
              </span>
            )}
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            {result.target_achieved ? "Final Match Score" : "Best Safe Score"}
          </span>
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-3xl font-extrabold text-emerald-400">
              {Math.round(result.final_score)}%
            </span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
          <span className="text-[10px] text-slate-500 mt-1">
            {result.iteration_count} optimization {result.iteration_count === 1 ? "step" : "steps"} applied
          </span>
        </div>
      </div>

      {/* Visual Progression Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-400 font-medium">
          <span className="flex items-center gap-1">
            <span>Score Shift:</span>
            <span className="text-slate-200 font-bold">{Math.round(result.original_score)}%</span>
            <ArrowRight className="w-3 h-3 text-slate-500" />
            <span className="text-emerald-400 font-bold">{Math.round(result.final_score)}%</span>
          </span>
          <span className="text-slate-400">Target Range: {result.target_min}%–{result.target_max}%</span>
        </div>
        <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800 relative">
          {/* Target Zone Highlight */}
          <div
            className="absolute top-0 bottom-0 bg-emerald-500/15 border-x border-emerald-500/40"
            style={{
              left: `${result.target_min}%`,
              width: `${result.target_max - result.target_min}%`,
            }}
          />
          {/* Final Score Bar */}
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, result.final_score))}%` }}
          />
        </div>
      </div>

      {/* Best Achievable / Plateau Explanation Alert (If Target Not Achieved) */}
      {!result.target_achieved && result.best_achievable_explanation && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/80 text-amber-200 text-xs space-y-1.5 leading-relaxed">
          <div className="flex items-center gap-2 font-bold text-amber-300">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>Honest Optimization Boundary: Non-Fabrication Guarantee</span>
          </div>
          <p className="text-slate-300 text-xs pl-6">
            {result.best_achievable_explanation}
          </p>
          <p className="text-[11px] text-amber-400/90 pl-6 italic">
            Note: This is an intentional safety boundary. The optimizer will never invent unsupported skills to artificially hit an ATS target.
          </p>
        </div>
      )}
    </div>
  );
};