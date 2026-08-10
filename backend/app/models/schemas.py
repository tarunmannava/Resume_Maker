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
    candidate_name: str
    company_name: str
    role_name: str


class RewriteRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    resume_latex: str = Field(..., min_length=20)
    candidate_name: str | None = None
    company_name: str | None = None
    role_name: str | None = None
    company_context: str | None = None
    rewrite_mode: RewriteMode = "transferable"
    target_match_threshold: int = 75
    confirmed_skills: list[str] = []
    banned_skills: list[str] = []
    extra_user_notes: str | None = None
    align_titles: bool = False
    selected_industry: str | None = None
    selected_role_category: str | None = None
    selected_stack_override: str | None = None


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
