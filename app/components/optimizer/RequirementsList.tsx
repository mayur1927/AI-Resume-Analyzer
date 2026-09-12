"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

interface RequirementsListProps {
  supportedRequirements: string[];
  unsupportedRequirements: string[];
}

export const RequirementsList: React.FC<RequirementsListProps> = ({
  supportedRequirements,
  unsupportedRequirements,
}) => {
  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Transparency / Non-fabrication banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 sm:p-5 flex items-start gap-3.5">
        <div className="w-8 h-8 rounded-lg bg-blue-950/70 border border-blue-800/60 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="space-y-1">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Requirement Evidence Classification
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            The optimizer categorizes job requirements into <strong className="text-emerald-300">Supported</strong> (grounded in your resume) and <strong className="text-amber-300">Unsupported</strong> (absent from your background).
          </p>
          <div className="p-2.5 mt-2 rounded-lg bg-slate-950/80 border border-amber-800/50 text-amber-300 text-xs font-semibold flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Unsupported requirements are not added to your resume.</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Supported Requirements */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                Supported Requirements ({supportedRequirements.length})
              </h4>
            </div>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-300">
              Evidenced
            </span>
          </div>

          {supportedRequirements.length > 0 ? (
            <div className="space-y-2">
              {supportedRequirements.map((req, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-2.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-200 leading-relaxed font-medium">
                    {req}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic py-4 text-center">
              No direct job requirements were evidenced in the baseline resume.
            </p>
          )}
        </div>

        {/* Unsupported Requirements */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                Unsupported Requirements ({unsupportedRequirements.length})
              </h4>
            </div>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-amber-950/80 border border-amber-700 text-amber-300">
              Not Evidenced
            </span>
          </div>

          {unsupportedRequirements.length > 0 ? (
            <div className="space-y-2">
              {unsupportedRequirements.map((req, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-2.5"
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="text-xs text-slate-300 leading-relaxed block">
                      {req}
                    </span>
                    <span className="text-[10px] text-amber-400/80 font-medium block">
                      • Omitted from optimized output to prevent resume fraud.
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-emerald-400 font-medium py-4 text-center">
              Full match: All job requirements were backed by evidence in your resume!
            </p>
          )}
        </div>
      </div>
    </div>
  );
};