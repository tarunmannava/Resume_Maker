from backend.app.services.rewrite_strategy import (
    build_rewrite_strategy,
    classify_target_role_identity,
)
from backend.app.services.projects_data import PROJECTS


SAMPLE_RESUME = """
Tarun Mannava
EXPERIENCE
University of South Florida Graduate Researcher React TypeScript Node.js Groq PostgreSQL
Cognizant Technology Solutions Java Spring Boot Redis MongoDB REST API 20K transactions
PROJECTS
Centralized Prompt Registry FastAPI
"""


def test_classify_backend_from_job_description():
    job = "Backend Software Engineer. Java, Spring Boot, REST APIs, Redis, PostgreSQL, microservices, scalability."
    role = classify_target_role_identity(job, SAMPLE_RESUME, "Software Engineer")
    assert role == "backend_engineer"


def test_classify_ai_platform_from_job():
    job = "LLM platform engineer. LangChain, RAG, inference serving, GPU, observability, evaluation pipelines."
    role = classify_target_role_identity(job, SAMPLE_RESUME, "AI Engineer")
    assert role == "ai_platform_engineer"


def test_build_rewrite_strategy_includes_priorities():
    job = "Backend engineer with Java Spring Boot Redis PostgreSQL REST APIs."
    strategy = build_rewrite_strategy(
        job,
        SAMPLE_RESUME,
        "Software Engineer",
        [PROJECTS[0], PROJECTS[2]],
        missing_terms=["Kubernetes"],
    )
    assert strategy.target_role == "backend_engineer"
    assert strategy.top_skills
    assert "Cognizant" in strategy.priority_experiences[0] or any(
        "Backend" in e for e in strategy.priority_experiences
    )
    assert strategy.prioritize
    assert strategy.de_emphasize
    block = strategy.to_prompt_block()
    assert "TARGET ROLE CLASSIFICATION:" in block
    assert "backend_engineer" in block
