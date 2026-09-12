"use client";

import React, { useState, useRef } from "react";
import { Upload, FileCheck, X, ChevronRight, RefreshCw, AlertTriangle, Info, Sliders, Sparkles, ShieldCheck, FileText } from "lucide-react";
import { TargetRangeSelector } from "./TargetRangeSelector";

interface OptimizerFormProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  jobDescription: string;
  onJobDescriptionChange: (jd: string) => void;
  targetMin: number;
  targetMax: number;
  onTargetMinChange: (val: number) => void;
  onTargetMaxChange: (val: number) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  error: string | null;
  onErrorDismiss: () => void;
}

const SAMPLE_JOB_DESCRIPTIONS = [
  {
    title: "Backend Engineer (Python & PostgreSQL)",
    description: `We are looking for a Backend Engineer with strong expertise in Python, FastAPI, PostgreSQL, Docker, and REST APIs.
Responsibilities:
- Build and optimize asynchronous backend microservices and databases.
- Design clean schema architectures and automate CI/CD deployments.
- Write thorough unit and integration tests with pytest.
Requirements:
- Proven experience in Python, SQL/PostgreSQL, Git, Linux, and Docker.
- Experience with API security, data modeling, and performance tuning.`,
  },
  {
    title: "Data Analyst (Python, SQL & Tableau)",
    description: `Seeking a Data Analyst proficient in Python, SQL, Tableau, Excel, and data visualization.
Responsibilities:
- Analyze large datasets to extract actionable business intelligence.
- Build interactive dashboards and automate weekly metric reporting.
- Communicate insights to cross-functional stakeholders.
Requirements:
- Strong SQL proficiency and experience with Python (pandas, numpy).
- Demonstrated experience in Tableau or PowerBI dashboards.`,
  },
];

export const OptimizerForm: React.FC<OptimizerFormProps> = ({
  file,
  onFileChange,
  jobDescription,
  onJobDescriptionChange,
  targetMin,
  targetMax,
  onTargetMinChange,
  onTargetMaxChange,
  onSubmit,
  isLoading,
  error,
  onErrorDismiss,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE_MB = 2;
  const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024;

  const handleFileInput = (selectedFile: File | null) => {
    if (!selectedFile) return;
    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      alert("Invalid format: Please upload a PDF file (.pdf)");
      return;
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      alert(`File too large: ${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB exceeds ${MAX_FILE_SIZE_MB} MB limit.`);
      return;
    }
    onFileChange(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileInput(e.dataTransfer.files[0]);
    }
  };

  return (
    <form onSubmit={onSubmit} className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-7 shadow-lg space-y-6">
      {/* Form Header */}
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <span>Resume Optimizer Configuration</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Select your source resume, job description, and desired ATS match range.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs flex items-start justify-between gap-3 animate-in fade-in duration-200">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{error}</span>
          </div>
          <button
            type="button"
            onClick={onErrorDismiss}
            className="text-rose-400 hover:text-rose-200 p-1 rounded hover:bg-rose-900/50"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Inputs: Resume PDF + Job Description */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Upload Box */}
        <div className="flex flex-col">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
            1. Resume Document (PDF)
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[220px] flex-1 ${
              isDragging
                ? "border-emerald-500 bg-emerald-950/20"
                : file
                ? "border-emerald-500/50 bg-emerald-950/10"
                : "border-slate-700 hover:border-slate-500 bg-slate-950/50 hover:bg-slate-950/80"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => handleFileInput(e.target.files?.[0] || null)}
            />

            {file ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <FileCheck className="w-5 h-5" />
                </div>
                <span className="font-semibold text-slate-100 text-xs max-w-[220px] truncate">
                  {file.name}
                </span>
                <span className="text-[11px] text-slate-400">
                  Size: {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready
                </span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onFileChange(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="mt-1 inline-flex items-center gap-1 text-[11px] text-rose-400 hover:text-rose-300 font-medium transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Remove file</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-slate-400">
                <div className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
                  <Upload className="w-5 h-5" />
                </div>
                <div className="text-xs font-medium text-slate-200">
                  Click to browse or drag & drop
                </div>
                <div className="text-[11px] text-slate-500">
                  PDF format only (Max {MAX_FILE_SIZE_MB}MB)
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Job Description Box */}
        <div className="flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
              2. Job Description
            </label>
            <span className="text-[10px] text-slate-500">
              {jobDescription.trim().length} chars
            </span>
          </div>

          <textarea
            value={jobDescription}
            onChange={(e) => onJobDescriptionChange(e.target.value)}
            placeholder="Paste complete job description requirements here..."
            className="w-full flex-1 min-h-[160px] p-3 text-xs bg-slate-950 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 resize-none font-mono"
          />

          {/* Sample JD Presets */}
          <div className="mt-2 flex items-center gap-2">
            <span className="text-[10px] text-slate-500 font-medium">Load sample:</span>
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_JOB_DESCRIPTIONS.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onJobDescriptionChange(s.description)}
                  className="px-2 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-colors"
                >
                  {s.title.split("(")[0].trim()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Target Range Selector */}
      <TargetRangeSelector
        targetMin={targetMin}
        targetMax={targetMax}
        onMinChange={onTargetMinChange}
        onMaxChange={onTargetMaxChange}
        disabled={isLoading}
      />

      {/* Pre-Optimization Verification Box */}
      <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400 shrink-0">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-200 block">Strict Non-Fabrication Rule Active</span>
            <p className="text-[11px] text-slate-400">
              Only evidenced skills and verifiable experiences from your uploaded resume will be targeted.
            </p>
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || !file || jobDescription.trim().length < 30}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white disabled:text-slate-500 text-xs font-bold transition-all shadow-md shadow-emerald-950/50 disabled:cursor-not-allowed shrink-0"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-white" />
              <span>Optimizing...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-emerald-200" />
              <span>Target {targetMin}%–{targetMax}% Match</span>
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </form>
  );
};
