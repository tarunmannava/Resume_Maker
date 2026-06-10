from backend.app.services.project_framing import (
    adapt_projects_to_job_description,
    extract_jd_foundational_concepts,
    extract_resume_supported_terms,
    select_projects,
)


def test_foundational_concepts_from_jd():
    jd = "Core Java, Collections, OOP, exception handling, Spring Boot, SQL debugging."
    concepts = extract_jd_foundational_concepts(jd)
    assert "OOP" in concepts
    assert "Core Java" in concepts
    assert any("exception" in c.lower() for c in concepts)


def test_resume_supported_terms_excludes_oracle_when_absent():
    resume = "Java Spring Boot PostgreSQL Redis MongoDB SQL Server"
    supported = extract_resume_supported_terms(resume)
    assert "java" in supported
    assert "oracle" not in supported


def test_projects_are_adapted_to_job_description_domain():
    jd = "Build secure banking payment APIs with Spring Boot, Redis caching, and SQL."
    projects = select_projects("Software Engineer", jd, "backend_engineer")
    adapted = adapt_projects_to_job_description(projects, jd, "Fintech", "backend_engineer")
    text = " ".join(" ".join(project["bullets"]) for project in adapted)

    assert "banking, payments, and fraud-prevention workflows" in text
    assert "Redis caching" in text or "Java/Spring Boot" in text
