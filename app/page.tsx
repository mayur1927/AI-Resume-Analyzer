"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  FileText,
  Upload,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Download,
  X,
  RefreshCw,
  Award,
  Layers,
  Search,
  LayoutTemplate,
  Info,
  Sliders,
  Cpu,
  Terminal,
  BookOpen,
  ChevronRight,
  ShieldCheck,
  Zap,
  History,
  Clock,
  PlusCircle,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { OptimizationResult, OptimizationHistoryItem } from "@/app/types/optimizer";
import { OptimizerForm } from "@/app/components/optimizer/OptimizerForm";
import { OptimizationLoading } from "@/app/components/optimizer/OptimizationLoading";
import { OptimizationResultView } from "@/app/components/optimizer/OptimizationResultView";
import { OptimizerHistory } from "@/app/components/optimizer/OptimizerHistory";


interface ScoreBreakdown {
  skill_match: number;
  keyword_match: number;
  sections: number;
  formatting: number;
}

interface AnalysisResult {
  analysis_id: string;
  filename: string;
  ats_score: number;
  score_breakdown: ScoreBreakdown;
  resume_skills: string[];
  job_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
  suggestions: string[];
  created_at?: string;
}

interface HistoryItem {
  analysis_id: string;
  filename: string;
  ats_score: number;
  created_at: string | null;
  matched_skills_count: number;
  missing_skills_count: number;
  matched_skills: string[];
}

const SAMPLE_JOB_DESCRIPTIONS = [
  {
    title: "Full Stack Engineer (Python & React)",
    description: `We are seeking a Full Stack Software Engineer proficient in Python, FastAPI, and React. 
Responsibilities:
- Build and maintain robust REST APIs using FastAPI, PostgreSQL, and Redis.
- Develop interactive and accessible frontend user interfaces with React, TypeScript, and modern CSS.
- Containerize and deploy services using Docker and Git CI/CD pipelines.
- Implement unit testing and ensure high code quality across the stack.

Qualifications:
- Strong experience in Python, SQL, PostgreSQL, and JavaScript/TypeScript.
- Experience with Docker, Linux environments, Git, and automated testing (pytest).
- Excellent problem-solving, communication, and software design skills.`,
  },
  {
    title: "Machine Learning / Data Engineer",
    description: `Looking for a Data / ML Engineer to develop data processing pipelines and NLP models.
Key Requirements:
- Proficient in Python, pandas, numpy, scikit-learn, and SQL.
- Experience with NLP frameworks (spaCy, NLTK) or machine learning libraries (pytorch, tensorflow).
- Strong understanding of ETL workflows, data analysis, and data visualization tools.
- Familiarity with cloud platforms (AWS/Azure/GCP) and containerization with Docker.`,
  },
];

export default function Home() {
  const [activeWorkflow, setActiveWorkflow] = useState<"analyze" | "optimize">("analyze");

  // Analyzer State
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isViewingHistory, setIsViewingHistory] = useState(false);
  const [historyList, setHistoryList] = useState<HistoryItem[]>([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [showArchModal, setShowArchModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Optimizer State
  const [optimizerFile, setOptimizerFile] = useState<File | null>(null);
  const [optimizerJobDescription, setOptimizerJobDescription] = useState("");
  const [targetMin, setTargetMin] = useState(80);
  const [targetMax, setTargetMax] = useState(85);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isLoadingOptimizerHistory, setIsLoadingOptimizerHistory] = useState(false);
  const [optimizerError, setOptimizerError] = useState<string | null>(null);
  const [optimizerResult, setOptimizerResult] = useState<OptimizationResult | null>(null);
  const [optimizerHistoryList, setOptimizerHistoryList] = useState<OptimizationHistoryItem[]>([]);
  const [isViewingOptimizerHistory, setIsViewingOptimizerHistory] = useState(false);
  const optimizerResultsRef = useRef<HTMLDivElement>(null);

  // Dynamically resolve API URL: explicit env var -> production relative path -> local dev backend
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL !== undefined
      ? process.env.NEXT_PUBLIC_API_URL
      : process.env.NODE_ENV === "production"
      ? ""
      : "http://127.0.0.1:8000";

  const MAX_FILE_SIZE_MB = 2;
  const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024; // 2 MB

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await fetch(`${API_URL}/api/analyses?limit=8`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setHistoryList(data);
      }
    } catch (err) {
      console.warn("Could not load analysis history:", err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const fetchOptimizerHistory = async () => {
    setIsLoadingOptimizerHistory(true);
    try {
      const response = await fetch(`${API_URL}/api/optimizations?limit=8`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setOptimizerHistoryList(data);
      }
    } catch (err) {
      console.warn("Could not load optimization history:", err);
    } finally {
      setIsLoadingOptimizerHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    fetchOptimizerHistory();
  }, []);

  const handleOptimizeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!optimizerFile) {
      setOptimizerError("Please select and upload a resume in PDF format.");
      return;
    }
    if (optimizerJobDescription.trim().length < 30) {
      setOptimizerError("Job description text is too short. Please provide at least 30 characters.");
      return;
    }
    if (targetMax <= targetMin) {
      setOptimizerError("Target maximum score must be greater than target minimum score.");
      return;
    }
    if (targetMax - targetMin < 5) {
      setOptimizerError("Target range span must be at least 5% (e.g. 80% – 85%).");
      return;
    }

    setIsOptimizing(true);
    setOptimizerError(null);
    setOptimizerResult(null);
    setIsViewingOptimizerHistory(false);

    const formData = new FormData();
    formData.append("resume", optimizerFile);
    formData.append("job_description", optimizerJobDescription);
    formData.append("target_min", targetMin.toString());
    formData.append("target_max", targetMax.toString());
    formData.append("max_iterations", "4");

    try {
      const response = await fetch(`${API_URL}/api/optimize`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      let data;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        throw new Error(
          !response.ok
            ? `Server Error (${response.status}): ${text.slice(0, 150)}`
            : "Received non-JSON response from server."
        );
      }

      if (!response.ok) {
        throw new Error(data?.detail || "Optimization processing failed on the server.");
      }

      setOptimizerResult(data);
      fetchOptimizerHistory();

      setTimeout(() => {
        optimizerResultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setOptimizerError(err.message);
      } else {
        setOptimizerError("Network Error: Unable to establish connection with the FastAPI backend service.");
      }
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleLoadOptimizationRecord = async (optimizationId: string) => {
    setIsOptimizing(true);
    setOptimizerError(null);
    try {
      const response = await fetch(`${API_URL}/api/optimizations/${optimizationId}`, {
        credentials: "include",
      });
      let data;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        throw new Error(`Failed to load historical record (HTTP ${response.status})`);
      }
      if (!response.ok) throw new Error(data?.detail || "Could not load historical optimization.");
      setOptimizerResult(data);
      setIsViewingOptimizerHistory(true);

      setTimeout(() => {
        optimizerResultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      setOptimizerError(err instanceof Error ? err.message : "Failed to load historical optimization record.");
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleResetOptimizer = () => {
    setOptimizerResult(null);
    setIsViewingOptimizerHistory(false);
    setOptimizerFile(null);
    setOptimizerError(null);
  };

  const handleFileChange = (selectedFile: File | null) => {
    if (!selectedFile) return;
    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Invalid file format: Please select a valid PDF document (.pdf). Non-PDF files are not supported.");
      return;
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(
        `File too large: Selected PDF is ${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB, which exceeds the ${MAX_FILE_SIZE_MB} MB limit.`
      );
      return;
    }
    setError(null);
    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select and upload a resume in PDF format.");
      return;
    }
    if (jobDescription.trim().length < 30) {
      setError("Job description text is too short. Please provide at least 30 characters.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setIsViewingHistory(false);

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_description", jobDescription);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      let data;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        throw new Error(
          !response.ok
            ? `Server Error (${response.status}): ${text.slice(0, 150)}`
            : "Received non-JSON response from server."
        );
      }

      if (!response.ok) {
        throw new Error(data?.detail || "Analysis processing failed on the server.");
      }

      setResult(data);
      fetchHistory(); // Refresh history list

      // Smooth scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Network Error: Unable to establish connection with the FastAPI backend service.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadHistoryItem = async (analysisId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/analyses/${analysisId}`, {
        credentials: "include",
      });
      let data;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        throw new Error(`Failed to load historical record (HTTP ${response.status})`);
      }
      if (!response.ok) throw new Error(data?.detail || "Could not load historical analysis.");
      setResult(data);
      setIsViewingHistory(true);

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load historical record.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setIsViewingHistory(false);
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setError(null);
  };

  const handleDownloadReport = async () => {
    if (!result?.analysis_id) return;
    setIsDownloading(true);
    try {
      const response = await fetch(`${API_URL}/api/analyses/${result.analysis_id}/report`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to download PDF report");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume-analysis-${result.analysis_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(err);
      alert("Failed to download evaluation report.");
    } finally {
      setIsDownloading(false);
    }
  };

  const getScoreRating = (score: number) => {
    if (score >= 80) return { label: "Strong ATS Alignment", color: "text-emerald-400", bg: "bg-emerald-950/60 border-emerald-700/60 text-emerald-300" };
    if (score >= 65) return { label: "Moderate ATS Alignment", color: "text-blue-400", bg: "bg-blue-950/60 border-blue-700/60 text-blue-300" };
    if (score >= 50) return { label: "Average Alignment", color: "text-amber-400", bg: "bg-amber-950/60 border-amber-700/60 text-amber-300" };
    return { label: "Low Alignment / Review Needed", color: "text-rose-400", bg: "bg-rose-950/60 border-rose-700/60 text-rose-300" };
  };

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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600/30 selection:text-blue-200">
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-bold">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base text-white tracking-tight">AI Resume Analyzer</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                  v1.0 • CE Final Year Project
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Intelligent Resume Analysis & Job Compatibility Assessment
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowArchModal(true)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors"
            >
              <Terminal className="w-3.5 h-3.5 text-blue-400" />
              <span>System Architecture</span>
            </button>
            <div className="hidden md:flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-950/50 border border-emerald-800/60 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>PostgreSQL Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Project Header Banner */}
        <section className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-xl p-6 sm:p-8">
          <div className="max-w-3xl">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Automated Resume Evaluation System
            </h1>
            <p className="mt-2 text-sm sm:text-base text-slate-300 leading-relaxed">
              An engineering platform designed to parse candidate resumes in PDF format, extract technical competencies via Natural Language Processing (spaCy deterministic PhraseMatcher), evaluate structural section headers, and quantify match metrics against specified job descriptions.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-400">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-blue-400" />
                <span>Deterministic Scoring Model</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>PostgreSQL Traceability</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>4-Dimensional ATS Heuristics</span>
              </div>
            </div>
          </div>
        </section>

        {/* Primary Workflow Switcher */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Tab 1: Analyze Resume */}
          <button
            type="button"
            onClick={() => setActiveWorkflow("analyze")}
            className={`p-5 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
              activeWorkflow === "analyze"
                ? "bg-slate-900 border-blue-500 ring-1 ring-blue-500/40 shadow-lg shadow-blue-950/40"
                : "bg-slate-900/50 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80 opacity-80 hover:opacity-100"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2.5">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    activeWorkflow === "analyze"
                      ? "bg-blue-600/20 text-blue-400 border border-blue-500/40"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  <Sliders className="w-4 h-4" />
                </div>
                <span className="font-bold text-sm sm:text-base text-white">1. Analyze Resume</span>
              </div>
              {activeWorkflow === "analyze" && (
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-800/60">
                  Active Workflow
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Check how well your resume matches a job description across 4 deterministic ATS dimensions.
            </p>
          </button>

          {/* Tab 2: Optimize Resume */}
          <button
            type="button"
            onClick={() => setActiveWorkflow("optimize")}
            className={`p-5 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
              activeWorkflow === "optimize"
                ? "bg-slate-900 border-emerald-500 ring-1 ring-emerald-500/40 shadow-lg shadow-emerald-950/40"
                : "bg-slate-900/50 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80 opacity-80 hover:opacity-100"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2.5">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    activeWorkflow === "optimize"
                      ? "bg-emerald-600/20 text-emerald-400 border border-emerald-500/40"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm sm:text-base text-white">2. Optimize Resume</span>
                  <span className="text-[10px] font-bold uppercase px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Phase 3
                  </span>
                </div>
              </div>
              {activeWorkflow === "optimize" ? (
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/60">
                  Active Workflow
                </span>
              ) : (
                <span className="text-xs text-emerald-400 font-semibold inline-flex items-center gap-1">
                  Target ATS Range <ChevronRight className="w-3.5 h-3.5" />
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Create a job-targeted version of your resume while preserving your real skills and experience.
            </p>
          </button>
        </div>

        {/* WORKFLOW 1: ANALYZE RESUME */}
        {activeWorkflow === "analyze" && (
          <div className="space-y-8">
            {/* Two-Column Grid: Left is Form, Right is Recent Analyses */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main Input Form Section (2 Columns on Large Screens) */}
              <section className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-7 shadow-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
                    <div>
                      <h2 className="text-base font-bold text-white flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-blue-400" />
                    <span>Analysis Parameters & Input Data</span>
                  </h2>
                  <p className="text-xs text-slate-400">Provide the candidate resume (PDF) and target job description.</p>
                </div>
                {result && (
                  <button
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 transition-colors"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    <span>New Analysis</span>
                  </button>
                )}
              </div>

              <form onSubmit={handleAnalyze} className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {/* Document Upload Box */}
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
                          ? "border-blue-500 bg-blue-950/20"
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
                        onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
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
                              setFile(null);
                              if (fileInputRef.current) fileInputRef.current.value = "";
                            }}
                            className="mt-1 inline-flex items-center gap-1 text-[11px] text-rose-400 hover:text-rose-300 font-medium transition-colors"
                          >
                            <X className="w-3.5 h-3.5" /> Remove Document
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2">
                          <div className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 mb-1">
                            <Upload className="w-5 h-5 text-blue-400" />
                          </div>
                          <p className="text-xs font-semibold text-slate-200">
                            Drop Resume PDF Here
                          </p>
                          <p className="text-[11px] text-slate-400">
                            Digital, text-readable PDF (Max 2 MB)
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Job Specification Input */}
                  <div className="flex flex-col">
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                        2. Target Job Description
                      </label>
                      <span className={`text-[11px] font-medium ${jobDescription.trim().length >= 30 ? "text-slate-400" : "text-amber-400"}`}>
                        {jobDescription.trim().length} chars (min 30)
                      </span>
                    </div>
                    <textarea
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste the target role responsibilities, required technical skills, and qualifications here..."
                      className="w-full flex-1 min-h-[170px] bg-slate-950/60 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                    />
                    {/* Sample Presets */}
                    <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-400">
                      <span className="font-medium shrink-0">Presets:</span>
                      <div className="flex flex-wrap gap-1">
                        {SAMPLE_JOB_DESCRIPTIONS.map((preset, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => setJobDescription(preset.description)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px] transition-colors"
                          >
                            {preset.title.split(" ")[0]} {preset.title.split(" ")[1]}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Error Message Alert */}
                {error && (
                  <div className="flex items-center gap-3 p-3.5 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-200 text-xs">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span className="flex-1 font-medium">{error}</span>
                    <button
                      type="button"
                      onClick={() => setError(null)}
                      className="text-rose-400 hover:text-rose-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}

                {/* Submit Action Bar */}
                <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800/80">
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>Runs deterministic spaCy token matching & commits record to PostgreSQL.</span>
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading || !file || jobDescription.trim().length < 30}
                    className={`w-full sm:w-auto px-6 py-2.5 rounded-lg font-semibold text-xs flex items-center justify-center gap-2 shadow-sm transition-all ${
                      isLoading || !file || jobDescription.trim().length < 30
                        ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                        : "bg-blue-600 hover:bg-blue-500 text-white active:scale-[0.99]"
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />
                        <span>Processing Document...</span>
                      </>
                    ) : (
                      <>
                        <span>Analyse Resume</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </section>

          {/* Right Column: Recent Analyses History Panel */}
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <History className="w-4 h-4 text-blue-400" />
                <span>Recent Analyses</span>
              </h3>
              <button
                onClick={fetchHistory}
                disabled={isLoadingHistory}
                title="Refresh history"
                className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingHistory ? "animate-spin" : ""}`} />
              </button>
            </div>

            <div className="flex-1 space-y-2 overflow-y-auto max-h-[380px] pr-1">
              {historyList.length > 0 ? (
                historyList.map((item) => {
                  const rating = getScoreRating(item.ats_score);
                  const isSelected = result?.analysis_id === item.analysis_id;
                  return (
                    <div
                      key={item.analysis_id}
                      onClick={() => handleLoadHistoryItem(item.analysis_id)}
                      className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                        isSelected
                          ? "bg-blue-950/40 border-blue-500/50 shadow-sm"
                          : "bg-slate-950/50 hover:bg-slate-950/80 border-slate-800/80 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-slate-200 truncate">
                            {item.filename}
                          </p>
                          <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-1">
                            <Clock className="w-3 h-3 text-slate-500" />
                            <span>{formatTimestamp(item.created_at)}</span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end shrink-0">
                          <span className={`text-xs font-extrabold px-2 py-0.5 rounded border ${rating.bg}`}>
                            {Math.round(item.ats_score)}/100
                          </span>
                        </div>
                      </div>

                      {item.matched_skills && item.matched_skills.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
                          <span className="truncate max-w-[170px]">
                            {item.matched_skills.slice(0, 3).join(", ")}
                            {item.matched_skills.length > 3 ? "..." : ""}
                          </span>
                          <span className="text-blue-400 font-medium inline-flex items-center gap-0.5 hover:underline">
                            Open <ExternalLink className="w-2.5 h-2.5" />
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8 px-4 text-xs text-slate-500">
                  <p>No historical evaluations found in PostgreSQL yet.</p>
                  <p className="text-[11px] text-slate-600 mt-1">Run an analysis to record your first entry.</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Empty State / How Pipeline Works (Shown When No Result is Selected) */}
        {!result && !isLoading && (
          <section className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 sm:p-8">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-400" />
              <span>Evaluation Methodology & Scoring Pipeline</span>
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 mb-6 max-w-2xl leading-relaxed">
              The analyzer evaluates documents across four discrete, explainable engineering dimensions:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                <div className="w-8 h-8 rounded-md bg-blue-950/60 border border-blue-800/60 flex items-center justify-center text-blue-400 text-xs font-bold mb-3">
                  60%
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-1">1. Skill Vocabulary Match</h4>
                <p className="text-xs text-slate-400 leading-normal">
                  Identifies technical tools, frameworks, and programming languages using exact-phrase token matching via spaCy PhraseMatcher.
                </p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                <div className="w-8 h-8 rounded-md bg-sky-950/60 border border-sky-800/60 flex items-center justify-center text-sky-400 text-xs font-bold mb-3">
                  20%
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-1">2. JD Keyword Alignment</h4>
                <p className="text-xs text-slate-400 leading-normal">
                  Calculates token intersection between the job description and candidate resume text after stop-word filtering.
                </p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                <div className="w-8 h-8 rounded-md bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 text-xs font-bold mb-3">
                  10%
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-1">3. Structural Sections</h4>
                <p className="text-xs text-slate-400 leading-normal">
                  Verifies standard ATS resume headers: Experience, Projects, Skills, Education, and Summary.
                </p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                <div className="w-8 h-8 rounded-md bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center text-emerald-400 text-xs font-bold mb-3">
                  10%
                </div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-1">4. Contact & Format Rules</h4>
                <p className="text-xs text-slate-400 leading-normal">
                  Validates email address syntax and overall text length bounds (250 – 12,000 characters).
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Output Evaluation Dashboard (Shown After Analysis or History Selection) */}
        {result && (
          <section ref={resultsRef} className="space-y-6 pt-2">
            {/* History Indicator Banner if loaded from database */}
            {isViewingHistory && (
              <div className="p-3 rounded-lg bg-blue-950/40 border border-blue-800/60 flex items-center justify-between text-xs text-blue-200">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-blue-400 shrink-0" />
                  <span>
                    Viewing saved evaluation from PostgreSQL: <b className="text-white">{result.filename}</b>
                    {result.created_at && ` (Recorded: ${formatTimestamp(result.created_at)})`}
                  </span>
                </div>
                <button
                  onClick={handleReset}
                  className="font-semibold text-blue-300 hover:text-white underline ml-4 shrink-0"
                >
                  Start New Analysis
                </button>
              </div>
            )}

            {/* Results Header Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-7 shadow-lg">
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-6 border-b border-slate-800">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
                  {/* Visual Score Indicator */}
                  <div className="w-28 h-28 rounded-xl bg-slate-950 border-2 border-slate-700 flex flex-col items-center justify-center p-3 shadow-inner shrink-0">
                    <span className={`text-3xl font-extrabold tracking-tight ${getScoreRating(result.ats_score).color}`}>
                      {Math.round(result.ats_score)}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                      / 100 PTS
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className={`text-xs px-2.5 py-0.5 rounded font-semibold border ${getScoreRating(result.ats_score).bg}`}>
                        {getScoreRating(result.ats_score).label}
                      </span>
                      <span className="text-xs text-slate-500">ID: {result.analysis_id.slice(0, 8)}</span>
                    </div>
                    <h3 className="text-xl font-bold text-white">ATS Compatibility Score</h3>
                    <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                      Target Resume: <span className="text-slate-200 font-semibold">{result.filename}</span>
                    </p>
                  </div>
                </div>

                {/* Download Report Button */}
                <button
                  onClick={handleDownloadReport}
                  disabled={isDownloading}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-all shadow-sm"
                >
                  {isDownloading ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
                  ) : (
                    <Download className="w-3.5 h-3.5 text-blue-400" />
                  )}
                  <span>Export Evaluation Report (.pdf)</span>
                </button>
              </div>

              {/* Progress Bar */}
              <div className="mt-6">
                <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium">
                  <span>Overall Match Progress</span>
                  <span>{Math.round(result.ats_score)}%</span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${Math.min(100, Math.max(0, result.ats_score))}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Score Breakdown (4-Card Metric Grid) */}
            <div>
              <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-400" />
                <span>Dimensional Score Breakdown</span>
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-medium">
                    <span>Skill Match</span>
                    <Award className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white">{result.score_breakdown?.skill_match ?? 0}</span>
                    <span className="text-xs text-slate-500">/ 60 pts</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2.5 overflow-hidden">
                    <div className="bg-blue-500 h-full rounded-full" style={{ width: `${((result.score_breakdown?.skill_match ?? 0) / 60) * 100}%` }} />
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-medium">
                    <span>Keyword Match</span>
                    <Search className="w-3.5 h-3.5 text-sky-400" />
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white">{result.score_breakdown?.keyword_match ?? 0}</span>
                    <span className="text-xs text-slate-500">/ 20 pts</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2.5 overflow-hidden">
                    <div className="bg-sky-500 h-full rounded-full" style={{ width: `${((result.score_breakdown?.keyword_match ?? 0) / 20) * 100}%` }} />
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-medium">
                    <span>Section Structure</span>
                    <LayoutTemplate className="w-3.5 h-3.5 text-cyan-400" />
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white">{result.score_breakdown?.sections ?? 0}</span>
                    <span className="text-xs text-slate-500">/ 10 pts</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2.5 overflow-hidden">
                    <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${((result.score_breakdown?.sections ?? 0) / 10) * 100}%` }} />
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-medium">
                    <span>Format & Email</span>
                    <FileText className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-bold text-white">{result.score_breakdown?.formatting ?? 0}</span>
                    <span className="text-xs text-slate-500">/ 10 pts</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2.5 overflow-hidden">
                    <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${((result.score_breakdown?.formatting ?? 0) / 10) * 100}%` }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Skills & Insights Detailed Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: Matched & Extracted Skills */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>Matched Competencies ({result.matched_skills?.length ?? 0})</span>
                    </h4>
                    <span className="text-[11px] text-emerald-400 font-semibold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                      Verified in Resume & JD
                    </span>
                  </div>
                  {result.matched_skills && result.matched_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {result.matched_skills.map((skill) => (
                        <span
                          key={skill}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-emerald-950/50 text-emerald-300 border border-emerald-800/60"
                        >
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                          <span>{skill}</span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No direct matching skills were detected from vocabulary.</p>
                  )}
                </div>

                <div className="pt-4 border-t border-slate-800">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                    All Detected Resume Skills ({result.resume_skills?.length ?? 0})
                  </h5>
                  {result.resume_skills && result.resume_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {result.resume_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2 py-0.5 rounded text-xs bg-slate-950 text-slate-300 border border-slate-800"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No known vocabulary skills found in resume.</p>
                  )}
                </div>
              </div>

              {/* Right Column: Missing Skills & Recommendations */}
              <div className="space-y-6">
                {/* Missing Skills Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      <span>Missing / Unmatched Skills ({result.missing_skills?.length ?? 0})</span>
                    </h4>
                    <span className="text-[11px] text-amber-400 font-semibold bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
                      Required by JD
                    </span>
                  </div>
                  {result.missing_skills && result.missing_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {result.missing_skills.map((skill) => (
                        <span
                          key={skill}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-amber-950/50 text-amber-300 border border-amber-800/60"
                        >
                          <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                          <span>{skill}</span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-emerald-400 font-medium">Full Coverage: All required skills from the job description were identified in the resume.</p>
                  )}
                </div>

                {/* Suggestions Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                    <Zap className="w-4 h-4 text-blue-400" />
                    <span>Optimization Recommendations</span>
                  </h4>
                  <ul className="space-y-2">
                    {result.suggestions && result.suggestions.length > 0 ? (
                      result.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs sm:text-sm text-slate-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0 mt-2" />
                          <span className="leading-relaxed">{suggestion}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-xs text-slate-400 italic">No specific suggestions generated.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </section>
        )}
          </div>
        )}

        {/* WORKFLOW 2: OPTIMIZE RESUME */}
        {activeWorkflow === "optimize" && (
          <div className="space-y-8">
            {/* Loading State */}
            {isOptimizing && (
              <OptimizationLoading targetMin={targetMin} targetMax={targetMax} />
            )}

            {/* Optimization Result Dashboard */}
            {optimizerResult && !isOptimizing && (
              <div ref={optimizerResultsRef} className="space-y-6">
                <OptimizationResultView
                  result={optimizerResult}
                  onReset={handleResetOptimizer}
                  isViewingHistory={isViewingOptimizerHistory}
                />
              </div>
            )}

            {/* Form and History Grid (Shown when not loading and no active result) */}
            {!optimizerResult && !isOptimizing && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Optimizer Form (2 Cols) */}
                <div className="lg:col-span-2">
                  <OptimizerForm
                    file={optimizerFile}
                    onFileChange={setOptimizerFile}
                    jobDescription={optimizerJobDescription}
                    onJobDescriptionChange={setOptimizerJobDescription}
                    targetMin={targetMin}
                    targetMax={targetMax}
                    onTargetMinChange={setTargetMin}
                    onTargetMaxChange={setTargetMax}
                    onSubmit={handleOptimizeSubmit}
                    isLoading={isOptimizing}
                    error={optimizerError}
                    onErrorDismiss={() => setOptimizerError(null)}
                  />
                </div>

                {/* Optimizer History Sidebar (1 Col) */}
                <div className="lg:col-span-1">
                  <OptimizerHistory
                    historyList={optimizerHistoryList}
                    isLoading={isLoadingOptimizerHistory}
                    onRefresh={fetchOptimizerHistory}
                    onSelect={handleLoadOptimizationRecord}
                    selectedId={null}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* System Architecture Modal */}
      {showArchModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 sm:p-7 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={() => setShowArchModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800 hover:bg-slate-700"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2.5 mb-4">
              <Terminal className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-bold text-white">System Architecture & Technical Specs</h3>
            </div>
            <div className="space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300">
                <span className="text-blue-400">Frontend:</span> Next.js 14 (App Router) + TypeScript + Tailwind CSS<br />
                <span className="text-sky-400">Backend API:</span> FastAPI + Uvicorn (Asynchronous REST)<br />
                <span className="text-emerald-400">NLP Engine:</span> spaCy v3.8.4 (PhraseMatcher) + Regex Tokenizer<br />
                <span className="text-indigo-400">Database:</span> PostgreSQL with SQLAlchemy 2.0 (JSONB Storage)<br />
                <span className="text-amber-400">Report Engine:</span> ReportLab (Print-Ready PDF Generation)
              </div>
              <p>
                <strong>Pipeline Execution Flow:</strong>
              </p>
              <ol className="list-decimal pl-5 space-y-1.5 text-xs text-slate-400">
                <li><strong>Document Parsing:</strong> The uploaded PDF is processed in-memory via <code className="text-slate-200">pypdf.PdfReader</code>.</li>
                <li><strong>Skill Extraction:</strong> spaCy&apos;s PhraseMatcher scans raw text against canonical tech skill vocabularies.</li>
                <li><strong>Keyword Overlap:</strong> Regex word tokenization computes Jaccard-style token intersection with the job description.</li>
                <li><strong>Structure & Quality:</strong> Regular expressions verify section headings and email contact formats.</li>
                <li><strong>Persistence:</strong> The computed evaluation is committed to PostgreSQL with a unique UUID and listed in Recent Analyses.</li>
              </ol>
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowArchModal(false)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-lg transition-colors"
              >
                Close Specifications
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            AI Resume Analyzer • Computer Engineering Capstone Project
          </div>
          <div className="flex items-center gap-4">
            <span>FastAPI REST Backend</span>
            <span>•</span>
            <span>spaCy NLP Engine</span>
            <span>•</span>
            <span>PostgreSQL Data Store</span>
            <span>•</span>
            <span>ReportLab PDF Engine</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
