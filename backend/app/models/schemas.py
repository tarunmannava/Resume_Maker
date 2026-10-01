from typing import Literal

from pydantic import BaseModel, Field

RewriteMode = Literal["strict", "transferable", "user_verified", "aggressive"]
KeywordStatus = Literal["exact", "transferable", "missing", "unsupported"]


class KeywordItem(BaseModel):
    term: str
    category: str
    weight: float = 1.0
    required: bool = False
    evidence_count: int = 1

class ScreeningAnswerRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    resume_latex: str = Field(..., min_length=20)
    question: str = Field(..., min_length=3)
    company_context: str | None = None
    role_name: str | None = None
    company_name: str | None = None


class ScreeningAnswerResponse(BaseModel):
    question: str
    answer: str
    warning: str | None = None


class KeywordMatch(BaseModel):
    term: str
    category: str
    weight: float
    status: KeywordStatus
    evidence: str | None = None
    risk: Literal["low", "medium", "high"] = "low"


class AnalyzeJobRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    company_context: str | None = None


class AnalyzeJobResponse(BaseModel):
    keywords: list[KeywordItem]
    required_keywords: list[str]
    preferred_keywords: list[str]
    seniority_signals: list[str]
    detected_industry: str | None = None
    detected_role_category: str | None = None
    warnings: list[str] = []


class AnalyzeResumeRequest(BaseModel):
    resume_latex: str = Field(..., min_length=20)


class AnalyzeResumeResponse(BaseModel):
    extracted_text: str
    keywords: list[KeywordItem]
    sections_found: list[str]
    ats_warnings: list[str]


class ScoreRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    resume_latex: str = Field(..., min_length=20)
    rewrite_mode: RewriteMode = "transferable"
    confirmed_skills: list[str] = []


class ScoreResponse(BaseModel):
    match_score: float
    target_met: bool
    matched_keywords: list[KeywordMatch]
    missing_keywords: list[KeywordMatch]
    unsupported_keywords: list[KeywordMatch]
    warnings: list[str]


class CompileRequest(BaseModel):
    latex_code: str = Field(..., min_length=20)
    candidate_name: str = "Tarun Mannava"
    company_name: str = "Company"
    role_name: str = "Software Engineer"


class RewriteRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    resume_latex: str = Field(..., min_length=20)
    candidate_name: str | None = None
    company_name: str | None = None
    role_name: str | None = None
    company_context: str | None = None
    rewrite_mode: RewriteMode = "transferable"
    target_match_threshold: int = 100
    confirmed_skills: list[str] = []
    banned_skills: list[str] = []
    extra_user_notes: str | None = None
    align_titles: bool = False
    selected_industry: str | None = None
    selected_role_category: str | None = None
    selected_stack_override: str | None = None
    target_stack: str | None = None
    target_location: str | None = None


class RewriteResponse(BaseModel):
    rewritten_latex: str
    match_score: float
    target_met: bool
    matched_keywords: list[KeywordMatch]
    missing_keywords: list[KeywordMatch]
    unsupported_keywords: list[KeywordMatch]
    warnings: list[str]
    changes_made: list[str]


# Removed RewriteCompileResponse as requested.


class ScreenJobRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    title: str | None = None
    company: str | None = None
    location: str | None = None
    technical_tools: list[str] | None = None


class ScreenJobResponse(BaseModel):
    eligible: bool
    flag_reason: str | None = None
    primary_stack: str | None = None
    confidence: float = 1.0
    explanation: str


class CapturedJob(BaseModel):
    id: str
    title: str
    company: str
    location: str | None = None
    apply_url: str | None = None
    description_text: str | None = None
    requirements_summary: str | None = None
    technical_tools: list[str] | None = None
    yoe: float | None = None
    seniority: str | None = None


class CaptureBatchRequest(BaseModel):
    jobs: list[CapturedJob]


class CaptureBatchResponse(BaseModel):
    added: int
    duplicates: int
    total_submitted: int


class KnownIdsRequest(BaseModel):
    ids: list[str]


class KnownIdsResponse(BaseModel):
    known_ids: list[str]


class QueueJob(BaseModel):
    id: str
    title: str
    company: str
    location: str | None = None
    apply_url: str | None = None
    description_text: str | None = None
    requirements_summary: str | None = None
    technical_tools: list[str] | None = None
    yoe: float | None = None
    seniority: str | None = None
    status: str
    primary_stack: str | None = None
    flag_reason: str | None = None
    screen_explanation: str | None = None
    match_score: float | None = None
    docx_url: str | None = None
    error: str | None = None
    captured_at: str
    updated_at: str
    applied_via_simplify: bool | None = None


class QueueStatusUpdateRequest(BaseModel):
    status: str
    applied_via_simplify: bool | None = None
    flag_reason: str | None = None
    screen_explanation: str | None = None


class QueueSimplifyToggleRequest(BaseModel):
    applied_via_simplify: bool


class QueueStatsResponse(BaseModel):
    queued: int
    screening: int
    rewriting: int
    ready: int
    low_match: int = 0
    flagged: int
    rejected: int
    failed: int
    applied: int
    dismissed: int
    total: int
    worker_running: bool = True


class FlagGuardrailRequest(BaseModel):
    reason: str
    overlooked_text: str | None = None


class ScreeningGuardrailItem(BaseModel):
    id: int
    job_id: str
    job_title: str
    company: str
    reason: str
    overlooked_text: str | None = None
    created_at: str


