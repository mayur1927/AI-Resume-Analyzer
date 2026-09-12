"use client";

import React, { useState } from "react";
import { OptimizationResult } from "@/app/types/optimizer";
import { ScoreComparison } from "./ScoreComparison";
import { ResumePreview } from "./ResumePreview";
import { ChangesList } from "./ChangesList";
import { RequirementsList } from "./RequirementsList";
import { PlusCircle, FileText, ListChecks, CheckCircle2, Download, Edit3, Share2, History } from "lucide-react";

interface OptimizationResultViewProps {
  result: OptimizationResult;
  onReset: () => void;
  isViewingHistory?: boolean;
}

export const OptimizationResultView: React.FC<OptimizationResultViewProps> = ({
  result,
  onReset,
  isViewingHistory = false,
}) => {
  const [activeTab, setActiveTab] = useState<"preview" | "changes" | "requirements">("preview");

  const changesList = result.changes || result.changes_applied || [];
  const resumeText = result.final_resume_text || result.optimized_resume_content || "";
  const filename = result.filename || "Resume";

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={onReset}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>Optimize Another Resume</span>
          </button>
          {isViewingHistory && (
            <div className="flex items-center gap-1.5 text-xs text-blue-400 bg-blue-950/60 border border-blue-800/50 px-3 py-1.5 rounded-lg">
              <History className="w-3.5 h-3.5" />
              <span>Viewing Saved Optimization Record</span>
            </div>
          )}
        </div>

        {/* Phase 4 Action Buttons Placeholder */}
        <div className="flex items-center gap-2">
          <button
            disabled
            title="Resume editor coming in Phase 4"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-500 text-xs font-medium cursor-not-allowed opacity-75"
          >
            <Edit3 className="w-3 h-3" />
            <span>Edit Resume</span>
            <span className="text-[9px] uppercase px-1 rounded bg-slate-800 text-slate-400">P4</span>
          </button>
          <button
            disabled
            title="PDF export coming in Phase 4"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-500 text-xs font-medium cursor-not-allowed opacity-75"
          >
            <Download className="w-3 h-3" />
            <span>Download PDF</span>
            <span className="text-[9px] uppercase px-1 rounded bg-slate-800 text-slate-400">P4</span>
          </button>
          <button
            disabled
            title="Share link coming in Phase 4"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-500 text-xs font-medium cursor-not-allowed opacity-75"
          >
            <Share2 className="w-3 h-3" />
            <span>Share</span>
            <span className="text-[9px] uppercase px-1 rounded bg-slate-800 text-slate-400">P4</span>
          </button>
        </div>
      </div>

      {/* Score Comparison Hero Card */}
      <ScoreComparison result={result} />

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab("preview")}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === "preview"
              ? "bg-emerald-950/70 border border-emerald-600 text-emerald-300 ring-1 ring-emerald-500/40"
              : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Formatted Resume Preview</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("changes")}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === "changes"
              ? "bg-emerald-950/70 border border-emerald-600 text-emerald-300 ring-1 ring-emerald-500/40"
              : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          }`}
        >
          <ListChecks className="w-4 h-4" />
          <span>Changes Made ({changesList.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("requirements")}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === "requirements"
              ? "bg-emerald-950/70 border border-emerald-600 text-emerald-300 ring-1 ring-emerald-500/40"
              : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>Requirements Matrix ({(result.supported_requirements || []).length} Supported)</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="pt-2">
        {activeTab === "preview" && (
          <ResumePreview
            resumeContent={resumeText}
            filename={filename}
          />
        )}

        {activeTab === "changes" && (
          <ChangesList
            changes={changesList}
            iterations={result.iterations}
          />
        )}

        {activeTab === "requirements" && (
          <RequirementsList
            supportedRequirements={result.supported_requirements || []}
            unsupportedRequirements={result.unsupported_requirements || []}
          />
        )}
      </div>
    </div>
  );
};