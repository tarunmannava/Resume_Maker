import hashlib
import logging
import re
import threading
import time
from typing import Any

from ..core.config import get_settings
from ..models.schemas import RewriteRequest, ScreenJobRequest
from .job_queue import claim_next, requeue_interrupted, update_job
from .pdf import compile_latex_to_docx
from .rewrite import clean_professional_title, get_archetype_latex, rewrite_resume
from .screening_classifier import hard_disqualifier, screen_job_with_ai

logger = logging.getLogger("uvicorn.error")

_worker_thread: threading.Thread | None = None
_stop_event = threading.Event()
_worker_lock = threading.Lock()


def _map_target_stack(raw_stack: str) -> str:
    if raw_stack in ("c#", "csharp", ".net", "dotnet"):
        return "dotnet"
    if raw_stack in ("java", "spring"):
        return "java"
    if raw_stack in ("node", "nodejs", "typescript", "javascript", "react"):
        return "node"
    if raw_stack in ("python", "fastapi", "django"):
        return "python"
    return "ai"


AI_DESCRIPTION_CHARS = 7500


def _job_description_for_ai(job: dict[str, Any], title: str, company: str, location: str) -> str:
    desc = job.get("description_text") or ""
    if len(desc) >= 20:
        return desc[:AI_DESCRIPTION_CHARS]
    # Description fetch failed in the extension; fall back to HiringCafe's structured summary.
    tools = job.get("technical_tools") or []
    parts = [f"Role: {title}", f"Company: {company}", f"Location: {location}"]
    if job.get("requirements_summary"):
        parts.append(f"Requirements: {job['requirements_summary']}")
    if isinstance(tools, list) and tools:
        parts.append(f"Technologies: {', '.join(str(t) for t in tools)}")
    return "\n".join(parts)


def process_one_job(job: dict[str, Any]) -> None:
    job_id = job["id"]
    title = job.get("title") or "Unknown Role"
    company = job.get("company") or "Company"
    location = job.get("location") or "United States"
    tools = job.get("technical_tools") or []
    jd_text = _job_description_for_ai(job, title, company, location)

    logger.info("Worker starting job %s: '%s' @ '%s'", job_id, title, company)

    try:
        if job.get("skip_screening"):
            # "Rewrite anyway": the user overrode the AI flag, so don't screen again.
            target_stack = _map_target_stack((job.get("primary_stack") or "ai").lower().strip())
            screen_explanation = job.get("screen_explanation")
        else:
            # Step 0: rule-based disqualifiers (no AI call needed)
            hard_flag = hard_disqualifier(title, job.get("description_text") or "")
            if hard_flag:
                flag_reason, explanation = hard_flag
                logger.info("Job %s flagged by rule: [%s] %s", job_id, flag_reason, explanation)
                update_job(job_id, status="flagged", flag_reason=flag_reason, screen_explanation=explanation)
                return

            # Step 1: AI Screening
            screen_req = ScreenJobRequest(
                job_description=jd_text,
                title=title,
                company=company,
                location=location,
                technical_tools=tools if isinstance(tools, list) else None,
            )
            screen_res = screen_job_with_ai(screen_req)

            raw_stack = (screen_res.primary_stack or "ai").lower().strip()

            # Check for ineligibility or disqualified stacks
            if not screen_res.eligible or raw_stack in ("cpp", "hardware"):
                flag_reason = screen_res.flag_reason
                if not flag_reason:
                    if raw_stack == "cpp":
                        flag_reason = "Exclusive C/C++"
                    elif raw_stack == "hardware":
                        flag_reason = "Hardware/FPGA"
                    else:
                        flag_reason = "Disqualified"

                logger.info("Job %s flagged: [%s] %s", job_id, flag_reason, screen_res.explanation)
                update_job(
                    job_id,
                    status="flagged",
                    flag_reason=flag_reason,
                    screen_explanation=screen_res.explanation,
                    primary_stack=raw_stack,
                )
                return

            target_stack = _map_target_stack(raw_stack)
            screen_explanation = screen_res.explanation

        # Step 2: Set status to rewriting and tailor resume
        logger.info("Job %s eligible. Target stack: %s. Rewriting...", job_id, target_stack)
        update_job(
            job_id,
            status="rewriting",
            primary_stack=target_stack,
            screen_explanation=screen_explanation,
        )

        base_latex = get_archetype_latex(target_stack)
        clean_title = clean_professional_title(title, target_stack)
        rewrite_req = RewriteRequest(
            job_description=jd_text,
            resume_latex=base_latex,
            candidate_name="Tarun Mannava",
            company_name=company,
            role_name=clean_title,
            target_stack=target_stack,
            rewrite_mode="transferable",
            target_match_threshold=100,
        )
        rewrite_res = rewrite_resume(rewrite_req)

        # Step 3: Compile to DOCX. HiringCafe ids share long prefixes ("adhoc___..."),
        # so hash the id to keep filenames unique per job.
        short_id = hashlib.sha1(job_id.encode("utf-8")).hexdigest()[:6]
        safe_company = re.sub(r"[^a-zA-Z0-9 ]", " ", company).strip()[:35] or "Company"
        role_for_filename = f"{title} {short_id}"

        docx_info = compile_latex_to_docx(
            latex_code=rewrite_res.rewritten_latex,
            candidate_name="Tarun Mannava",
            company_name=safe_company,
            role_name=role_for_filename,
        )

        if hasattr(docx_info, "docx_download_url"):
            docx_url = docx_info.docx_download_url
        elif isinstance(docx_info, dict):
            docx_url = docx_info.get("docx_download_url") or docx_info.get("file_url")
        else:
            docx_url = None
        if not docx_url:
            errors = getattr(docx_info, "errors", None) or []
            raise RuntimeError("DOCX generation failed" + (f": {'; '.join(errors)}" if errors else ""))
        score = rewrite_res.match_score
        target_status = "ready" if (score is not None and score >= 70.0) else "low_match"
        logger.info(
            "Job %s complete! Status: %s with DOCX: %s (Score: %s)",
            job_id,
            target_status,
            docx_url,
            score,
        )

        update_job(
            job_id,
            status=target_status,
            match_score=score,
            docx_url=docx_url,
            error=None,
            skip_screening=0,
        )

    except Exception as exc:
        logger.error("Job worker error processing %s: %s", job_id, exc, exc_info=True)
        update_job(job_id, status="failed", error=str(exc))


def _worker_loop() -> None:
    logger.info("Job queue worker daemon started.")
    while not _stop_event.is_set():
        try:
            job = claim_next()
            if job:
                process_one_job(job)
            else:
                _stop_event.wait(timeout=3.0)
        except Exception as exc:
            logger.error("Unexpected error in worker loop: %s", exc, exc_info=True)
            _stop_event.wait(timeout=3.0)

    logger.info("Job queue worker daemon stopped.")


def start_worker() -> None:
    global _worker_thread
    with _worker_lock:
        settings = get_settings()
        if not settings.queue_worker_enabled:
            logger.info("Queue worker is disabled via config (queue_worker_enabled=False).")
            return

        if _worker_thread and _worker_thread.is_alive():
            logger.info("Queue worker thread is already running.")
            return

        requeued = requeue_interrupted()
        if requeued > 0:
            logger.info("Requeued %d interrupted jobs back to 'queued' state.", requeued)

        _stop_event.clear()
        _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="JobQueueWorker")
        _worker_thread.start()
        logger.info("Queue worker thread launched successfully.")


def stop_worker() -> None:
    global _worker_thread
    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            logger.info("Stopping queue worker thread...")
            _stop_event.set()
            _worker_thread.join(timeout=5.0)
            _worker_thread = None


def is_worker_running() -> bool:
    return bool(_worker_thread and _worker_thread.is_alive())
