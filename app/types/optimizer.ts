export interface ChangeRecord {
  section: string;
  original_text: string;
  optimized_text: string;
  reason: string;
  evidence_used?: string;
  evidence?: string;
  change_type: string;
}

export interface OptimizationIteration {
  iteration_number?: number;
  iteration?: number;
  ats_score?: number;
  score_after?: number;
  applied_operation?: string;
  score_delta?: number;
  summary?: string;
  changes_in_iteration?: ChangeRecord[];
  target_met?: boolean;
}

export interface OptimizationResult {
  optimization_id: string;
  id?: string;
  analysis_id?: string | null;
  original_score: number;
  target_min: number;
  target_max: number;
  final_score: number;
  target_achieved: boolean;
  iteration_count: number;
  original_resume_text?: string;
  final_resume_text?: string;
  optimized_resume_content?: string;
  unsupported_requirements: string[];
  supported_requirements: string[];
  changes?: ChangeRecord[];
  changes_applied?: ChangeRecord[];
  iterations?: OptimizationIteration[];
  optimization_summary?: string;
  best_achievable_explanation?: string | null;
  created_at?: string | null;
  filename?: string;
  job_description?: string;
}

export interface OptimizationHistoryItem {
  optimization_id: string;
  analysis_id: string | null;
  target_min: number;
  target_max: number;
  original_score: number;
  final_score: number;
  target_achieved: boolean;
  iteration_count: number;
  created_at: string | null;
}