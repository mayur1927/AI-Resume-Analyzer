"use client";

import React, { useState } from "react";
import { Copy, Check, FileText, Download, Eye } from "lucide-react";

interface ResumePreviewProps {
  resumeContent: string;
  filename: string;
}

export const ResumePreview: React.FC<ResumePreviewProps> = ({ resumeContent, filename }) => {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<"formatted" | "plain">("formatted");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(resumeContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy resume content", err);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-7 shadow-lg space-y-4 animate-in fade-in duration-200">
      {/* Action header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Targeted Resume Preview</h3>
            <p className="text-xs text-slate-400">Derived from {filename}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode Switcher */}
          <div className="bg-slate-950 p-0.5 rounded-lg border border-slate-800 flex items-center">
            <button
              type="button"
              onClick={() => setViewMode("formatted")}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                viewMode === "formatted"
                  ? "bg-slate-800 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Document View
            </button>
            <button
              type="button"
              onClick={() => setViewMode("plain")}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                viewMode === "plain"
                  ? "bg-slate-800 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Plain Text
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-300">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>Copy Content</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Document Sheet / Content Area */}
      {viewMode === "formatted" ? (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 sm:p-8 font-sans text-slate-200 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap selection:bg-emerald-600/30 max-h-[600px] overflow-y-auto shadow-inner">
          {resumeContent}
        </div>
      ) : (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-[600px] overflow-y-auto">
          {resumeContent}
        </div>
      )}
    </div>
  );
};