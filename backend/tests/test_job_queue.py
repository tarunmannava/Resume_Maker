import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.job_queue import (
    add_jobs,
    claim_next,
    get_job,
    init_db,
    known_ids,
    list_jobs,
    requeue_interrupted,
    retry_job,
    set_db_path,
    set_job_status,
    stats,
    update_job,
)
from backend.app.services.job_worker import process_one_job
from backend.app.services.screening_classifier import hard_disqualifier, infer_primary_stack
from backend.app.models.schemas import ScreenJobResponse, RewriteResponse


@pytest.fixture
def temp_db(tmp_path):
    test_db = tmp_path / "test_jobs.db"
    set_db_path(test_db)
    init_db(test_db)
    yield test_db
    set_db_path(None)


def test_add_jobs_and_deduplication(temp_db):
    batch = [
        {
            "id": "job-1",
            "title": "Software Engineer",
            "company": "Acme Corp",
            "location": "Remote",
            "description_text": "<p>We need a Python engineer</p>",
            "technical_tools": ["Python", "Docker"],
            "yoe": 2.0,
        },
        {
            "id": "job-2",
            "title": "Java Developer",
            "company": "Beta LLC",
            "location": "Chicago, IL",
            "description_text": "Spring Boot microservices",
            "technical_tools": ["Java", "Spring Boot"],
        },
    ]

    added, duplicates = add_jobs(batch, db_path=temp_db)
    assert added == 2
    assert duplicates == 0

    # Repeat capture of same batch
    added2, duplicates2 = add_jobs(batch, db_path=temp_db)
    assert added2 == 0
    assert duplicates2 == 2

    # Check known_ids
    found = known_ids(["job-1", "job-3"], db_path=temp_db)
    assert found == ["job-1"]


def test_claim_next_and_requeue_interrupted(temp_db):
    batch = [
        {"id": "job-a", "title": "Role A", "company": "Comp A"},
        {"id": "job-b", "title": "Role B", "company": "Comp B"},
    ]
    add_jobs(batch, db_path=temp_db)

    # Claim first job
    claimed = claim_next(db_path=temp_db)
    assert claimed is not None
    assert claimed["id"] == "job-a"
    assert claimed["status"] == "screening"

    # Next claim should be job-b
    claimed2 = claim_next(db_path=temp_db)
    assert claimed2 is not None
    assert claimed2["id"] == "job-b"

    # No more queued
    assert claim_next(db_path=temp_db) is None

    # Simulate interruption and restart
    update_job("job-b", db_path=temp_db, status="rewriting")
    requeued_count = requeue_interrupted(db_path=temp_db)
    assert requeued_count == 2  # job-a was 'screening', job-b was 'rewriting'

    # Should be back in queue
    reclaimed = claim_next(db_path=temp_db)
    assert reclaimed is not None
    assert reclaimed["id"] == "job-a"


def test_worker_eligible_job_flow(temp_db, monkeypatch):
    add_jobs([{"id": "test-eligible", "title": "Python Dev", "company": "Tech Inc", "description_text": "Python FastAPI"}], db_path=temp_db)
    job = claim_next(db_path=temp_db)

    # Mock screen_job_with_ai
    mock_screen = MagicMock(return_value=ScreenJobResponse(
        eligible=True,
        flag_reason=None,
        primary_stack="python",
        confidence=0.95,
        explanation="Strong fit for Python backend",
    ))
    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_screen)

    # Mock rewrite_resume
    mock_rewrite = MagicMock(return_value=RewriteResponse(
        rewritten_latex="\\documentclass{article}\\begin{document}Rewritten\\end{document}",
        match_score=92.5,
        target_met=True,
        matched_keywords=[],
        missing_keywords=[],
        unsupported_keywords=[],
        warnings=[],
        changes_made=[],
    ))
    monkeypatch.setattr("backend.app.services.job_worker.rewrite_resume", mock_rewrite)

    # Mock compile_latex_to_docx
    mock_docx = MagicMock(return_value={
        "status": "success",
        "docx_download_url": "/api/files/generated/Tarun_Mannava_Tech_Inc_Python_Dev.docx",
    })
    monkeypatch.setattr("backend.app.services.job_worker.compile_latex_to_docx", mock_docx)

    process_one_job(job)

    updated = get_job("test-eligible", db_path=temp_db)
    assert updated is not None
    assert updated["status"] == "ready"
    assert updated["match_score"] == 92.5
    assert updated["docx_url"] == "/api/files/generated/Tarun_Mannava_Tech_Inc_Python_Dev.docx"
    assert updated["primary_stack"] == "python"


def test_worker_ineligible_flagged_job_flow(temp_db, monkeypatch):
    add_jobs([{"id": "test-flagged", "title": "C++ Kernel Dev", "company": "Firmware Corp", "description_text": "Requires Top Secret"}], db_path=temp_db)
    job = claim_next(db_path=temp_db)

    mock_screen = MagicMock(return_value=ScreenJobResponse(
        eligible=False,
        flag_reason="Security Clearance",
        primary_stack="cpp",
        confidence=0.99,
        explanation="Applicant requires active DoD clearance",
    ))
    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_screen)

    process_one_job(job)

    updated = get_job("test-flagged", db_path=temp_db)
    assert updated is not None
    assert updated["status"] == "flagged"
    assert updated["flag_reason"] == "Security Clearance"
    assert "clearance" in updated["screen_explanation"].lower()


def test_worker_exception_sets_failed(temp_db, monkeypatch):
    add_jobs([{"id": "test-fail", "title": "Crashing Role", "company": "Bug Co"}], db_path=temp_db)
    job = claim_next(db_path=temp_db)

    def mock_raise(*args, **kwargs):
        raise RuntimeError("OpenAI connection timed out")

    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_raise)

    process_one_job(job)

    updated = get_job("test-fail", db_path=temp_db)
    assert updated is not None
    assert updated["status"] == "failed"
    assert "OpenAI connection timed out" in updated["error"]


def _mock_rewrite_response():
    return RewriteResponse(
        rewritten_latex="\\documentclass{article}\\begin{document}Rewritten\\end{document}",
        match_score=90.0,
        target_met=True,
        matched_keywords=[],
        missing_keywords=[],
        unsupported_keywords=[],
        warnings=[],
        changes_made=[],
    )


def test_force_retry_of_flagged_job_skips_screening(temp_db, monkeypatch):
    add_jobs([{"id": "adhoc___acme___1", "title": "Embedded Dev", "company": "Acme", "description_text": "C++ firmware work"}], db_path=temp_db)
    update_job("adhoc___acme___1", db_path=temp_db, status="flagged", flag_reason="Exclusive C/C++", primary_stack="cpp")

    assert retry_job("adhoc___acme___1", force=True, db_path=temp_db)
    job = claim_next(db_path=temp_db)

    mock_screen = MagicMock()
    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_screen)
    monkeypatch.setattr("backend.app.services.job_worker.rewrite_resume", MagicMock(return_value=_mock_rewrite_response()))
    monkeypatch.setattr(
        "backend.app.services.job_worker.compile_latex_to_docx",
        MagicMock(return_value={"docx_download_url": "/api/files/x/y.docx"}),
    )

    process_one_job(job)

    mock_screen.assert_not_called()
    updated = get_job("adhoc___acme___1", db_path=temp_db)
    assert updated["status"] == "ready"
    assert updated["primary_stack"] == "ai"
    assert updated["skip_screening"] == 0


def test_docx_filenames_are_unique_for_shared_id_prefixes(temp_db, monkeypatch):
    ids = ["adhoc___tastytrade___111", "adhoc___tastytrade___222"]
    add_jobs([{"id": i, "title": "Software Engineer", "company": "tastytrade", "description_text": "Python services"} for i in ids], db_path=temp_db)

    monkeypatch.setattr(
        "backend.app.services.job_worker.screen_job_with_ai",
        MagicMock(return_value=ScreenJobResponse(eligible=True, flag_reason=None, primary_stack="python", confidence=0.9, explanation="fit")),
    )
    monkeypatch.setattr("backend.app.services.job_worker.rewrite_resume", MagicMock(return_value=_mock_rewrite_response()))
    mock_docx = MagicMock(return_value={"docx_download_url": "/api/files/x/y.docx"})
    monkeypatch.setattr("backend.app.services.job_worker.compile_latex_to_docx", mock_docx)

    process_one_job(claim_next(db_path=temp_db))
    process_one_job(claim_next(db_path=temp_db))

    role_names = [c.kwargs["role_name"] for c in mock_docx.call_args_list]
    assert len(set(role_names)) == 2


def test_missing_docx_marks_job_failed(temp_db, monkeypatch):
    add_jobs([{"id": "no-docx", "title": "Dev", "company": "Co", "description_text": "Java Spring Boot APIs"}], db_path=temp_db)
    monkeypatch.setattr(
        "backend.app.services.job_worker.screen_job_with_ai",
        MagicMock(return_value=ScreenJobResponse(eligible=True, flag_reason=None, primary_stack="java", confidence=0.9, explanation="fit")),
    )
    monkeypatch.setattr("backend.app.services.job_worker.rewrite_resume", MagicMock(return_value=_mock_rewrite_response()))
    monkeypatch.setattr(
        "backend.app.services.job_worker.compile_latex_to_docx",
        MagicMock(return_value={"docx_download_url": None}),
    )

    process_one_job(claim_next(db_path=temp_db))

    updated = get_job("no-docx", db_path=temp_db)
    assert updated["status"] == "failed"
    assert "DOCX generation failed" in updated["error"]


def test_list_jobs_accepts_multiple_statuses(temp_db):
    add_jobs([{"id": f"j{i}", "title": "T", "company": "C"} for i in range(3)], db_path=temp_db)
    update_job("j1", db_path=temp_db, status="rewriting")
    update_job("j2", db_path=temp_db, status="ready")

    in_progress = list_jobs(status="queued,screening,rewriting", db_path=temp_db)
    assert sorted(j["id"] for j in in_progress) == ["j0", "j1"]


@pytest.mark.parametrize(
    "title,jd,expected",
    [
        ("Software Engineer Intern", "Python work", "Internship"),
        ("Software Engineering Internship - Summer 2027", "Java", "Internship"),
        ("Software Engineer Co-op", "Java", "Internship"),
        ("Software Engineer", "Candidates must hold an active Secret clearance.", "Security Clearance"),
        ("Software Engineer", "TS/SCI with polygraph preferred.", "Security Clearance"),
        ("Software Engineer", "Must be a U.S. citizen due to contract requirements.", "Citizenship Required"),
        ("Software Engineer", "This position is subject to ITAR regulations.", "Export Control"),
        ("Software Engineer", "Qualified applicants receive consideration without regard to citizenship status.", None),
        ("Software Engineer", "No security clearance required. Python and AWS.", None),
        ("Internal Tools Engineer", "Build internal platforms in Python.", None),
        ("Software Engineer", "Work with international teams on Java services.", None),
        (
            "Software Developer",
            "Please note, the City of Glendale does not sponsor any employment-based immigrant visas.  "
            "Applicants must be currently authorized to work in the United States on a full-time basis.",
            "No Sponsorship",
        ),
        ("Software Engineer", "We are unable to sponsor H-1B visas for this role.", "No Sponsorship"),
        ("Software Engineer", "Visa sponsorship is not available for this position.", "No Sponsorship"),
        ("Software Engineer", "Must be authorized to work in the U.S. without sponsorship.", "No Sponsorship"),
        (
            "Software Engineer",
            "Candidates who require visa sponsorship now or in the future will not be considered.",
            "No Sponsorship",
        ),
        ("Software Engineer", "Visa sponsorship is available for qualified candidates.", None),
        ("Software Engineer", "We sponsor H-1B and green cards.", None),
        ("Software Engineer", "No prior experience needed, and we sponsor visas.", None),
        (
            "AI Software Engineer",
            "Due to compliance with U.S. export control laws and regulations, candidate must be a U.S. Person, "
            "which is defined as, a U.S. citizen, a U.S. permanent resident, or have protected status in the U.S. "
            "under asylum or refugee status OR have the ability to obtain an export authorization.",
            "Export Control",
        ),
        ("Software Engineer", "Applicants must be a U.S. person.", "Export Control"),
        ("Software Engineer", "Visa sponsorship available; relocation not available.", None),
        ("Software Engineer, GPU Performance", "Python and PyTorch.", "GPU/HPC Performance"),
        (
            "Software Engineer",
            "Strong curiosity about GPU hardware, including memory bandwidth, cache behavior, tensor cores. "
            "Experience with CUDA, Triton, or C++ GPU programming.",
            "GPU/HPC Performance",
        ),
        (
            "Machine Learning Engineer",
            "Train and serve PyTorch models on GPUs. Experience with CUDA or Triton is a plus.",
            None,
        ),
        ("Software Engineer", "Future sponsorship for work authorization is not available.", "No Sponsorship"),
        (
            "Software Engineer",
            "We consider all applicants regardless of race, citizenship, or any other legally protected status.",
            None,
        ),
        ("Software Engineer", "No visa sponsorship is offered for this role.", "No Sponsorship"),
        (
            "Senior Fleet Software Engineer",
            "Strong proficiency in Python plus at least one systems language (Go, C++, or Rust).",
            "Systems Language",
        ),
        ("Software Engineer", "Python as well as Go required for production services.", "Systems Language"),
        ("Software Engineer", "Proficiency in Java, Python, or C++.", None),
        ("Software Engineer", "Experience with Python, C++, Go, and Java is a plus.", None),
    ],
)
def test_hard_disqualifier(title, jd, expected):
    result = hard_disqualifier(title, jd)
    assert (result[0] if result else None) == expected


@pytest.mark.parametrize(
    "title,jd,expected",
    [
        (
            "Software Engineer",
            "Strong TypeScript skills, including async programming. Experience writing unit tests "
            "for JavaScript/TypeScript. You'll refactor legacy Python, C#, and Visual Basic "
            "applications into a clean TypeScript/Node.js stack. Build LLM API integrations and RAG.",
            "node",
        ),
        (
            "Software Engineer",
            "Unit tests for JavaScript. REST APIs and React dashboards.",
            "node",
        ),
        ("Java Developer", "Spring Boot microservices and PostgreSQL.", "java"),
        ("Software Engineer", "C# and ASP.NET Core Web APIs with SQL Server.", "dotnet"),
        ("Backend Engineer", "Python FastAPI services and PostgreSQL.", "python"),
    ],
)
def test_infer_primary_stack_does_not_treat_javascript_as_java(title, jd, expected):
    assert infer_primary_stack(title, jd) == expected


def test_clean_html_description_separates_list_items():
    from backend.app.services.job_queue import clean_html_description

    text = clean_html_description("<ul><li>Active TS/SCI with Polygraph</li><li>Bachelor's degree</li></ul>")
    assert "Polygraph\nBachelor's" in text


def test_sponsorship_note_at_end_of_long_description_is_flagged(temp_db, monkeypatch):
    long_desc = ("Build Python services and React dashboards. " * 250) + "Sponsorship will not be provided for this role."
    assert len(long_desc) > 7500
    add_jobs([{"id": "long-1", "title": "Software Engineer", "company": "Co", "description_text": long_desc}], db_path=temp_db)
    mock_screen = MagicMock()
    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_screen)

    process_one_job(claim_next(db_path=temp_db))

    mock_screen.assert_not_called()
    assert get_job("long-1", db_path=temp_db)["flag_reason"] == "No Sponsorship"


def test_worker_flags_internship_without_calling_ai(temp_db, monkeypatch):
    add_jobs([{"id": "intern-1", "title": "Software Engineer Intern", "company": "Acme", "description_text": "Python and React work"}], db_path=temp_db)
    mock_screen = MagicMock()
    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_screen)

    process_one_job(claim_next(db_path=temp_db))

    mock_screen.assert_not_called()
    updated = get_job("intern-1", db_path=temp_db)
    assert updated["status"] == "flagged"
    assert updated["flag_reason"] == "Internship"


def test_queue_routes_api(temp_db):
    client = TestClient(app)

    # 1. Capture batch
    capture_payload = {
        "jobs": [
            {
                "id": "api-job-1",
                "title": "Backend Engineer",
                "company": "Stripe",
                "location": "Seattle, WA",
                "description_text": "Java and Distributed Systems",
                "technical_tools": ["Java", "Kafka"],
            },
            {
                "id": "api-job-2",
                "title": "Full Stack Engineer",
                "company": "Netflix",
                "location": "Remote",
                "description_text": "Node.js and React",
            },
        ]
    }
    res = client.post("/api/queue/capture", json=capture_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["added"] == 2
    assert data["duplicates"] == 0

    # 2. Known IDs
    known_res = client.post("/api/queue/known", json={"ids": ["api-job-1", "api-job-99"]})
    assert known_res.status_code == 200
    assert known_res.json()["known_ids"] == ["api-job-1"]

    # 3. List jobs
    list_res = client.get("/api/queue/jobs")
    assert list_res.status_code == 200
    jobs = list_res.json()
    assert len(jobs) == 2

    # 4. Stats
    stats_res = client.get("/api/queue/stats")
    assert stats_res.status_code == 200
    s_data = stats_res.json()
    assert s_data["queued"] == 2
    assert s_data["total"] == 2

    # 5. Status update (applied) - defaults to applied_via_simplify = False (0, Tailored)
    status_res = client.post("/api/queue/jobs/api-job-1/status", json={"status": "applied"})
    assert status_res.status_code == 200

    job_1 = client.get("/api/queue/jobs/api-job-1").json()
    assert job_1["status"] == "applied"
    assert job_1["applied_via_simplify"] is False

    # 5b. Toggle simplify flag to True (1, Simplify)
    toggle_res = client.post("/api/queue/jobs/api-job-1/simplify", json={"applied_via_simplify": True})
    assert toggle_res.status_code == 200
    job_1_simplify = client.get("/api/queue/jobs/api-job-1").json()
    assert job_1_simplify["applied_via_simplify"] is True

    # 5c. Toggle simplify flag back to False (0, Tailored)
    toggle_back = client.post("/api/queue/jobs/api-job-1/simplify", json={"applied_via_simplify": False})
    assert toggle_back.status_code == 200
    job_1_tailored = client.get("/api/queue/jobs/api-job-1").json()
    assert job_1_tailored["applied_via_simplify"] is False

    # 6. Retry
    retry_res = client.post("/api/queue/jobs/api-job-1/retry?force=true")
    assert retry_res.status_code == 200
    job_1_after = client.get("/api/queue/jobs/api-job-1").json()
    assert job_1_after["status"] == "queued"

    # 7. Manual flag for security clearance with reason and explanation
    flag_res = client.post(
        "/api/queue/jobs/api-job-2/status",
        json={
            "status": "flagged",
            "flag_reason": "Security Clearance",
            "screen_explanation": "Manually flagged from Ready tab: Security clearance requirement overlooked",
        },
    )
    assert flag_res.status_code == 200
    job_2_flagged = client.get("/api/queue/jobs/api-job-2").json()
    assert job_2_flagged["status"] == "flagged"
    assert job_2_flagged["flag_reason"] == "Security Clearance"
    assert "clearance requirement overlooked" in job_2_flagged["screen_explanation"]


def test_worker_low_match_job_flow(temp_db, monkeypatch):
    add_jobs([{"id": "test-low-score", "title": "DevOps Engineer", "company": "Cloud Co", "description_text": "Kubernetes and Go"}], db_path=temp_db)
    job = claim_next(db_path=temp_db)

    mock_screen = MagicMock(return_value=ScreenJobResponse(
        eligible=True,
        flag_reason=None,
        primary_stack="python",
        confidence=0.9,
        explanation="Eligible",
    ))
    monkeypatch.setattr("backend.app.services.job_worker.screen_job_with_ai", mock_screen)

    mock_rewrite = MagicMock(return_value=RewriteResponse(
        rewritten_latex="\\documentclass{article}\\begin{document}Rewritten\\end{document}",
        match_score=58.0,  # Below 70% threshold
        target_met=False,
        matched_keywords=[],
        missing_keywords=[],
        unsupported_keywords=[],
        warnings=[],
        changes_made=[],
    ))
    monkeypatch.setattr("backend.app.services.job_worker.rewrite_resume", mock_rewrite)

    mock_docx = MagicMock(return_value={
        "status": "success",
        "docx_download_url": "/api/files/generated/Tarun_Mannava_Cloud_Co_DevOps.docx",
    })
    monkeypatch.setattr("backend.app.services.job_worker.compile_latex_to_docx", mock_docx)

    process_one_job(job)

    updated = get_job("test-low-score", db_path=temp_db)
    assert updated is not None
    assert updated["status"] == "low_match"
    assert updated["match_score"] == 58.0
    assert updated["docx_url"] == "/api/files/generated/Tarun_Mannava_Cloud_Co_DevOps.docx"

    # Verify stats includes low_match
    s = stats(db_path=temp_db)
    assert s["low_match"] == 1


def test_screening_clearance_expanded_regex():
    assert hard_disqualifier("Engineer", "Position requires Public Trust clearance.")[0] == "Security Clearance"
    assert hard_disqualifier("Backend Dev", "Must hold or be eligible for DoD Secret clearance.")[0] == "Security Clearance"
    assert hard_disqualifier("Software Engineer", "Subject to government security investigation and clearance.")[0] == "Security Clearance"
    assert hard_disqualifier("Dev", "Candidate must demonstrate security clearance eligibility upon hire.")[0] == "Security Clearance"


def test_screening_guardrails_db_and_api(temp_db):
    client = TestClient(app)
    add_jobs([{"id": "guardrail-job-1", "title": "Defense Analyst", "company": "Lockheed", "description_text": "Requires CI Polygraph"}], db_path=temp_db)

    # 1. API: Post guardrail
    res = client.post(
        "/api/queue/jobs/guardrail-job-1/guardrail",
        json={
            "reason": "Security Clearance",
            "overlooked_text": "Must hold active CI Polygraph",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["guardrail"]["job_id"] == "guardrail-job-1"
    assert data["guardrail"]["reason"] == "Security Clearance"
    assert data["guardrail"]["overlooked_text"] == "Must hold active CI Polygraph"

    # Verify job status was updated
    j = get_job("guardrail-job-1", db_path=temp_db)
    assert j["status"] == "flagged"
    assert j["flag_reason"] == "Security Clearance"
    assert "CI Polygraph" in j["screen_explanation"]

    # 2. API: List guardrails
    list_res = client.get("/api/queue/guardrails")
    assert list_res.status_code == 200
    guardrails = list_res.json()
    assert len(guardrails) >= 1
    assert guardrails[0]["job_id"] == "guardrail-job-1"

    # 3. Test check_custom_guardrails matches the snippet
    from backend.app.services.screening_classifier import check_custom_guardrails
    match = check_custom_guardrails("This position says: Must hold active CI Polygraph before start date.")
    assert match is not None
    assert match[0] == "Security Clearance"
    assert "CI Polygraph" in match[1]


def test_screen_job_with_ai_injects_golden_guardrails(temp_db, monkeypatch):
    from backend.app.services.job_queue import add_screening_guardrail
    from backend.app.services.screening_classifier import screen_job_with_ai
    from backend.app.models.schemas import ScreenJobRequest

    add_screening_guardrail(
        job_id="test-guardrail-prompt",
        reason="Security Clearance",
        overlooked_text="Must hold active TS/SCI polygraph",
        db_path=temp_db,
    )

    captured_prompt = {}

    class MockCompletion:
        def __init__(self, content):
            self.choices = [MagicMock(message=MagicMock(content=content))]

    def mock_create(*args, **kwargs):
        messages = kwargs.get("messages", [])
        for m in messages:
            if m.get("role") == "system":
                captured_prompt["system"] = m.get("content", "")
        return MockCompletion('{"eligible": false, "flag_reason": "Security Clearance", "primary_stack": "python", "confidence": 0.99, "explanation": "Requires TS/SCI polygraph"}')

    monkeypatch.setattr("backend.app.services.screening_classifier.OpenAI", lambda *args, **kwargs: MagicMock(chat=MagicMock(completions=MagicMock(create=mock_create))))

    req = ScreenJobRequest(
        title="Software Engineer",
        company="GovTech",
        job_description="Standard software engineer role",
    )
    resp = screen_job_with_ai(req)
    assert resp.eligible is False
    assert "HUMAN CORRECTIONS & GOLDEN GUARDRAILS" in captured_prompt.get("system", "")
    assert "Must hold active TS/SCI polygraph" in captured_prompt.get("system", "")



