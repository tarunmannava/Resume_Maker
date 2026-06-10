from backend.app.services.keyword_extractor import extract_keywords
from backend.app.services.scoring import score_keywords


def test_cplusplus_from_java_is_high_risk_transferable():
    job = "Required: C++ development, data structures, algorithms, multithreading."
    resume = "Built Java backend services using object-oriented programming, data structures, algorithms, and multithreading."
    keywords = extract_keywords(job, job_context=True)

    result = score_keywords(keywords, resume, rewrite_mode="transferable")

    assert result.match_score > 0
    assert any(
        match.term == "c++" and match.status == "transferable"
        for match in result.matched_keywords
    )
    assert any(item.term == "c++" for item in result.unsupported_keywords)


def test_exact_python_django_match():
    job = "Required Python and Django REST Framework experience with PostgreSQL."
    resume = "Developed Python Django REST Framework APIs with PostgreSQL."
    keywords = extract_keywords(job, job_context=True)

    result = score_keywords(keywords, resume, rewrite_mode="strict")

    assert result.match_score == 100
    assert result.target_met
