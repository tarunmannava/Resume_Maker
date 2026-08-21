export type RewriteMode =
  | "strict"
  | "transferable"
  | "user_verified"
  | "aggressive";

export type KeywordMatch = {
  term: string;
  category: string;
  weight: number;
  status: "exact" | "transferable" | "missing" | "unsupported";
  evidence?: string | null;
  risk: "low" | "medium" | "high";
};

// Removed PDF compilation types as requested.

export type RewriteRequest = {
  job_description: string;
  resume_latex: string;
  candidate_name?: string | null;
  company_name?: string | null;
  role_name?: string | null;
  company_context?: string | null;
  rewrite_mode: RewriteMode;
  target_match_threshold: number;
  confirmed_skills: string[];
  banned_skills: string[];
  extra_user_notes?: string | null;
  align_titles?: boolean;
  selected_industry?: string | null;
  selected_role_category?: string | null;
  selected_stack_override?: string | null;
};

export type RewriteResponse = {
  rewritten_latex: string;
  match_score: number;
  target_met: boolean;
  matched_keywords: KeywordMatch[];
  missing_keywords: KeywordMatch[];
  unsupported_keywords: KeywordMatch[];
  warnings: string[];
  changes_made: string[];
};

export type AnalyzeJobRequest = {
  job_description: string;
  company_context?: string | null;
};

export type AnalyzeJobResponse = {
  keywords: any[];
  required_keywords: string[];
  preferred_keywords: string[];
  seniority_signals: string[];
  detected_industry: string | null;
  detected_role_category: string | null;
  warnings: string[];
};

export type CompileRequest = {
  latex_code: string;
  candidate_name: string;
  company_name: string;
  role_name: string;
};

export type CompileResponse = {
  success: boolean;
  filename_base: string;
  tex_path: string;
  pdf_path?: string | null;
  docx_path?: string | null;
  docx_download_url?: string | null;
  log_path?: string | null;
  pdf_download_url?: string | null;
  compiler?: string | null;
  errors: string[];
  warnings: string[];
};

export type ScreeningAnswerRequest = {
  job_description: string;
  resume_latex: string;
  question: string;
  company_context?: string | null;
  role_name?: string | null;
  company_name?: string | null;
};

export type ScreeningAnswerResponse = {
  question: string;
  answer: string;
  warning?: string | null;
};

const viteEnv = import.meta as ImportMeta & {
  env?: Record<string, string | undefined>;
};
const API_BASE_URL = viteEnv.env?.VITE_API_BASE_URL || "http://localhost:8000";

export function toAbsoluteApiUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}

export async function rewriteResume(
  payload: RewriteRequest,
): Promise<RewriteResponse> {
  const response = await fetch(`${API_BASE_URL}/api/rewrite`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      Pragma: "no-cache",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Rewrite failed with ${response.status}: ${detail}`,
    );
  }

  return response.json();
}

export async function analyzeJob(
  payload: AnalyzeJobRequest,
): Promise<AnalyzeJobResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze-job`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Analyze job failed with ${response.status}: ${detail}`,
    );
  }

  return response.json();
}

export async function compileLatex(
  payload: CompileRequest,
): Promise<CompileResponse> {
  const response = await fetch(`${API_BASE_URL}/api/compile`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Compilation failed: ${detail}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function answerScreeningQuestion(
  payload: ScreeningAnswerRequest,
): Promise<ScreeningAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/screening/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Screening answer failed with ${response.status}: ${detail}`,
    );
  }

  return response.json();
}
