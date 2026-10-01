from typing import Any
from fastapi import APIRouter, HTTPException, Query


from ..models.schemas import (
    CaptureBatchRequest,
    CaptureBatchResponse,
    KnownIdsRequest,
    KnownIdsResponse,
    QueueJob,
    QueueStatsResponse,
    QueueStatusUpdateRequest,
    QueueSimplifyToggleRequest,
    FlagGuardrailRequest,
    ScreeningGuardrailItem,
)
from ..services.job_queue import (
    add_jobs,
    get_job,
    known_ids,
    list_jobs,
    retry_job,
    set_job_status,
    toggle_job_simplify,
    stats,
    add_screening_guardrail,
    get_screening_guardrails,
)
from ..services.job_worker import is_worker_running

queue_router = APIRouter(prefix="/queue", tags=["Job Queue"])


@queue_router.post("/known", response_model=KnownIdsResponse)
def get_known_job_ids(request: KnownIdsRequest) -> KnownIdsResponse:
    """Returns IDs that are already present in the database to prevent redundant JD fetches."""
    already_known = known_ids(request.ids)
    return KnownIdsResponse(known_ids=already_known)


@queue_router.post("/capture", response_model=CaptureBatchResponse)
def capture_job_batch(request: CaptureBatchRequest) -> CaptureBatchResponse:
    """Accepts a batch of captured jobs from the Chrome extension and queues them for processing."""
    job_dicts = [j.model_dump() for j in request.jobs]
    added, duplicates = add_jobs(job_dicts)
    return CaptureBatchResponse(
        added=added,
        duplicates=duplicates,
        total_submitted=len(request.jobs),
    )


@queue_router.get("/jobs", response_model=list[QueueJob])
def get_queued_jobs(
    status: str | None = Query(None, description="Filter by status (ready, flagged, failed, etc.)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[QueueJob]:
    """Lists jobs ordered by captured_at descending."""
    raw_jobs = list_jobs(status=status, limit=limit, offset=offset)
    return [QueueJob(**j) for j in raw_jobs]


@queue_router.get("/jobs/{job_id}", response_model=QueueJob)
def get_single_queued_job(job_id: str) -> QueueJob:
    """Retrieves a single job by ID."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return QueueJob(**job)


@queue_router.get("/stats", response_model=QueueStatsResponse)
def get_queue_stats() -> QueueStatsResponse:
    """Returns summary statistics across all job statuses."""
    s = stats()
    return QueueStatsResponse(**s, worker_running=is_worker_running())


@queue_router.post("/jobs/{job_id}/status")
def update_job_status(job_id: str, request: QueueStatusUpdateRequest) -> dict[str, bool]:
    """Updates job status to 'applied', 'dismissed', 'flagged', etc. Defaults applied_via_simplify to False (0, Tailored) when applied."""
    success = set_job_status(
        job_id,
        request.status,
        applied_via_simplify=request.applied_via_simplify,
        flag_reason=request.flag_reason,
        screen_explanation=request.screen_explanation,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid status or job not found")
    return {"success": True}


@queue_router.post("/jobs/{job_id}/simplify")
def update_job_simplify(job_id: str, request: QueueSimplifyToggleRequest) -> dict[str, bool]:
    """Toggles whether an applied job was submitted via Simplify / Original resume or Tailored resume."""
    success = toggle_job_simplify(job_id, request.applied_via_simplify)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True}


@queue_router.post("/jobs/{job_id}/retry")
def retry_queued_job(job_id: str, force: bool = Query(False)) -> dict[str, bool]:
    """Requeues a failed or flagged job. Set force=True to force-apply/rewrite a flagged job."""
    success = retry_job(job_id, force=force)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True}


@queue_router.post("/jobs/{job_id}/guardrail")
def flag_job_with_guardrail(job_id: str, request: FlagGuardrailRequest) -> dict[str, Any]:
    """
    Flags a job with a user-provided reason and overlooked requirement snippet,
    saving it to the golden guardrails dataset for future screening alignment.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    guardrail = add_screening_guardrail(
        job_id=job_id,
        reason=request.reason,
        overlooked_text=request.overlooked_text,
    )
    return {"success": True, "guardrail": guardrail}


@queue_router.get("/guardrails", response_model=list[ScreeningGuardrailItem])
def list_screening_guardrails(limit: int = Query(50, ge=1, le=200)) -> list[ScreeningGuardrailItem]:
    """Returns stored golden guardrails."""
    raw = get_screening_guardrails(limit=limit)
    return [ScreeningGuardrailItem(**g) for g in raw]

