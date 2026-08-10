from backend.app.services.job_analyzer import detect_details_with_keywords
from backend.app.services.project_framing import materialize_project_for_identity, select_projects
from backend.app.services.rewrite import get_effective_industry, get_effective_role_category
from backend.app.services.projects_data import PROJECTS


def test_keyword_industry_detection():
    # Fintech keywords
    fintech_job = "Looking for a software engineer to build secure banking APIs and transaction ledgers, fraud prevention."
    industry, role = detect_details_with_keywords(fintech_job)
    assert industry == "Fintech"
    assert role == "Software Engineer"

    # Healthcare keywords
    health_job = "We need an engineer to process clinical medical records and patient data in HIPAA environments."
    industry, role = detect_details_with_keywords(health_job)
    assert industry == "Healthcare"
    assert role == "Software Engineer"

    # Cybersecurity keywords
    sec_job = "Seeking a specialist in cryptography, threat detection, and identity auth systems."
    industry, role = detect_details_with_keywords(sec_job)
    assert industry == "Cybersecurity"


def test_keyword_role_detection():
    # AI Engineer keywords
    ai_job = "Develop generative AI workflows using LLMs, LangChain, and vector databases like Pinecone."
    _, role = detect_details_with_keywords(ai_job)
    assert role == "AI Engineer"

    # ML Engineer keywords
    ml_job = "Train deep learning models in PyTorch, XGBoost, Scikit-learn for recommendations."
    _, role = detect_details_with_keywords(ml_job)
    assert role == "ML Engineer"

    # AI Support keywords
    ops_job = "Set up MLOps pipelines, model deployment and vLLM serving infrastructure on Kubernetes."
    _, role = detect_details_with_keywords(ops_job)
    assert role == "AI Support"


def test_project_selection_mapping():
    # AI Engineer should select Project 1 and 2
    ai_projects = select_projects("AI Engineer", "")
    assert len(ai_projects) == 2
    assert ai_projects[0]["id"] == 1
    assert ai_projects[1]["id"] == 2

    # Software Engineer should select 2 projects from pool
    swe_projects = select_projects("Software Engineer", "")
    assert len(swe_projects) == 2


def test_dynamic_project_selection_for_swe():
    swe_rag_job = "We need a Backend Developer to build Python APIs and integrate LLMs/RAG indexes."
    projects = select_projects("Software Engineer", swe_rag_job, "ai_platform_engineer")
    assert len(projects) == 2
    project_ids = [p["id"] for p in projects]
    assert 1 in project_ids

    swe_infra_job = "Looking for a backend dev with experience in Docker, REST APIs, and microservices."
    projects = select_projects("Software Engineer", swe_infra_job, "devops_engineer")
    project_ids = [p["id"] for p in projects]
    assert 2 in project_ids or 1 in project_ids


def test_junior_java_jd_selects_backend_fullstack_projects():
    java_job = (
        "Junior Java Developer. Core Java, Collections, OOP, exception handling, "
        "Spring Boot, REST APIs, SQL, debugging, web applications."
    )
    projects = select_projects("Software Engineer", java_job, "backend_engineer")
    ids = [p["id"] for p in projects]
    assert 3 in ids
    for p in projects:
        assert "LangGraph" not in " ".join(p["tech_stack"])
        assert "multi-agent" not in p["title"].lower()


def test_backend_framing_changes_agent_project_title():
    agent = next(p for p in PROJECTS if p["id"] == 2)
    framed = materialize_project_for_identity(agent, "backend_engineer")
    assert "Workflow" in framed["title"] or "Distributed" in framed["title"]
    assert "multi-agent" not in framed["title"].lower()
