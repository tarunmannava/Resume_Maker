import inspect

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from ..models.schemas import (
    AnalyzeJobRequest,
    AnalyzeJobResponse,
    AnalyzeResumeRequest,
    AnalyzeResumeResponse,
    CompileRequest,
    RewriteRequest,
    RewriteResponse,
    ScoreRequest,
    ScoreResponse,
    ScreeningAnswerRequest,
    ScreeningAnswerResponse,
)
from ..services.keyword_extractor import extract_keywords, seniority_signals
from ..services.latex import ats_warnings, find_sections, latex_to_text
from ..services.pdf import compile_latex_to_pdf, compile_latex_to_docx, resolve_generated_file
from ..services.rewrite import rewrite_resume
from ..services.scoring import score_keywords
from ..services.job_analyzer import detect_details_with_ai, resolve_industry
from ..services.screening import answer_screening_question

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str | bool]:
    from ..services import rewrite as rewrite_service

    return {
        "status": "ok",
        "rewrite_module": rewrite_service.__file__ or "",
        "project_guard_v3": "Post-process pipeline v3 active"
        in inspect.getsource(rewrite_service.rewrite_resume),
    }


@router.post("/analyze-job", response_model=AnalyzeJobResponse)
def analyze_job(request: AnalyzeJobRequest) -> AnalyzeJobResponse:
    text = request.job_description + "\n" + (request.company_context or "")
    keywords = extract_keywords(text, job_context=True)
    required = [item.term for item in keywords if item.required]
    preferred = [item.term for item in keywords if not item.required]
    
    detected_industry, industry_confidence, _ = resolve_industry(
        request.job_description,
        request.company_context,
    )
    _, detected_role_category = detect_details_with_ai(
        request.job_description, request.company_context
    )
    if industry_confidence < 0.35:
        detected_industry = None
    
    warnings: list[str] = []
    if not keywords:
        warnings.append(
            "No known technical keywords were detected. Expand the keyword catalog or provide more job text."
        )
    return AnalyzeJobResponse(
        keywords=keywords,
        required_keywords=required,
        preferred_keywords=preferred,
        seniority_signals=seniority_signals(text),
        detected_industry=detected_industry,
        detected_role_category=detected_role_category,
        warnings=warnings,
    )


@router.post("/analyze-resume", response_model=AnalyzeResumeResponse)
def analyze_resume(request: AnalyzeResumeRequest) -> AnalyzeResumeResponse:
    text = latex_to_text(request.resume_latex)
    return AnalyzeResumeResponse(
        extracted_text=text,
        keywords=extract_keywords(text),
        sections_found=find_sections(request.resume_latex),
        ats_warnings=ats_warnings(request.resume_latex),
    )


@router.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest) -> ScoreResponse:
    job_keywords = extract_keywords(request.job_description, job_context=True)
    resume_text = latex_to_text(request.resume_latex)
    return score_keywords(
        job_keywords,
        resume_text,
        rewrite_mode=request.rewrite_mode,
        confirmed_skills=request.confirmed_skills,
    )


@router.post("/rewrite", response_model=RewriteResponse)
def rewrite(request: RewriteRequest, response: Response) -> RewriteResponse:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return rewrite_resume(request)


@router.post("/compile")
def compile_latex(request: CompileRequest):
    result = compile_latex_to_pdf(
        latex_code=request.latex_code,
        candidate_name=request.candidate_name,
        company_name=request.company_name,
        role_name=request.role_name,
    )
    return result


@router.post("/compile-docx")
def compile_docx(request: CompileRequest):
    result = compile_latex_to_docx(
        latex_code=request.latex_code,
        candidate_name=request.candidate_name,
        company_name=request.company_name,
        role_name=request.role_name,
    )
    return result


@router.get("/files/{folder}/{filename}")
def get_file(folder: str, filename: str):
    file_path = resolve_generated_file(folder, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@router.post("/screening/answer", response_model=ScreeningAnswerResponse)
def screening_answer(request: ScreeningAnswerRequest) -> ScreeningAnswerResponse:
    answer, warning = answer_screening_question(
        request.resume_latex,
        request.job_description,
        request.question,
        company_context=request.company_context,
        role_name=request.role_name,
        company_name=request.company_name,
    )
    return ScreeningAnswerResponse(
        question=request.question,
        answer=answer,
        warning=warning,
    )
