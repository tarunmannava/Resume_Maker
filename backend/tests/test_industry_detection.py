from backend.app.services.industry_detector import detect_industry_from_text, normalize_industry
from backend.app.services.job_analyzer import detect_details_with_keywords, resolve_industry


def test_fintech_banking_job():
    job = "Build secure banking APIs, payment processing, fraud prevention, and ledger reconciliation."
    result = detect_industry_from_text(job)
    assert result.industry == "Fintech"
    assert result.confidence >= 0.55


def test_healthcare_hipaa_job():
    job = "Engineer for HIPAA-compliant EHR integration and clinical patient data workflows in hospital systems."
    result = detect_industry_from_text(job)
    assert result.industry == "Healthcare"
    assert result.confidence >= 0.55


def test_cybersecurity_job():
    job = "Seeking a specialist in cryptography, threat detection, vulnerability management, and SOC operations."
    result = detect_industry_from_text(job)
    assert result.industry == "Cybersecurity"


def test_not_healthcare_for_health_checks():
    job = "Implement health checks, uptime monitoring, and Spring Security with JWT authentication for REST APIs."
    result = detect_industry_from_text(job)
    assert result.industry != "Healthcare"


def test_not_cybersecurity_for_app_auth():
    job = "Build REST APIs with OAuth, JWT, Spring Security, and role-based access control for a B2B SaaS product."
    result = detect_industry_from_text(job)
    assert result.industry != "Cybersecurity"


def test_not_edtech_for_machine_learning():
    job = "Train deep learning and machine learning models using PyTorch for recommendation systems."
    result = detect_industry_from_text(job)
    assert result.industry != "Edtech"


def test_company_hint_tesla():
    job = "Software engineer for vehicle telemetry and embedded systems."
    result = detect_industry_from_text(job, company_context="Tesla Motors")
    assert result.industry == "Automotive"


def test_company_hint_stripe():
    result = detect_industry_from_text(
        "Backend engineer for distributed systems.",
        company_context="Stripe payments infrastructure team",
    )
    assert result.industry == "Fintech"


def test_resolve_industry_low_confidence_returns_default():
    job = "Software engineer. Write clean code. Collaborate with team."
    industry, confidence, source = resolve_industry(job)
    assert source == "default"
    assert industry == "General Technology"
    assert confidence == 0.0


def test_resolve_industry_user_override():
    industry, confidence, source = resolve_industry(
        "vague job", user_selected="Healthcare"
    )
    assert industry == "Healthcare"
    assert source == "user"
    assert confidence == 1.0


def test_keyword_wrapper_matches_legacy_tests():
    fintech_job = "Looking for a software engineer to build secure banking APIs and transaction ledgers, fraud prevention."
    industry, role = detect_details_with_keywords(fintech_job)
    assert industry == "Fintech"

    health_job = "We need an engineer to process clinical medical records and patient data in HIPAA environments."
    industry, _ = detect_details_with_keywords(health_job)
    assert industry == "Healthcare"


def test_normalize_industry_aliases():
    assert normalize_industry("financial services") == "Fintech"
    assert normalize_industry("HIPAA Healthcare") == "Healthcare"
