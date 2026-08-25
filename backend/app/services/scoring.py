from ..models.schemas import KeywordItem, KeywordMatch, ScoreResponse
from .keyword_extractor import keyword_pattern, normalize

EQUIVALENTS: dict[str, list[str]] = {
    "angular": ["react", "vue", "typescript", "component-based"],
    "react": ["angular", "vue", "typescript", "component-based"],
    "django": ["spring boot", "fastapi", "flask", "java", "rest api", "orm"],
    "django rest framework": ["spring boot", "fastapi", "flask", "rest api", "orm"],
    "spring boot": ["django", "fastapi", "flask", "rest api", "java"],
    "python": ["java", "backend", "scripting"],
    "java": ["python", "c++", "object-oriented", "oop"],
    "postgresql": ["mysql", "sql", "relational database"],
    "mysql": ["postgresql", "sql", "relational database"],
    "aws": ["gcp", "azure", "cloud"],
    "gcp": ["aws", "azure", "cloud"],
    "azure": ["aws", "gcp", "cloud"],
    "ci/cd": ["github actions", "jenkins", "deployment pipeline"],
    "kubernetes": ["docker", "containerization"],
    "c++": [
        "java",
        "object-oriented",
        "oop",
        "data structures",
        "algorithms",
        "multithreading",
        "performance",
    ],
    "c": ["data structures", "algorithms", "memory management", "systems programming"],
    # Data Engineering Equivalents
    "spark": ["pyspark", "hadoop", "kafka", "data processing"],
    "pyspark": ["spark", "hadoop", "kafka", "data processing"],
    "snowflake": ["bigquery", "redshift", "databricks", "data warehouse"],
    "bigquery": ["snowflake", "redshift", "databricks", "data warehouse"],
    "redshift": ["snowflake", "bigquery", "databricks", "data warehouse"],
    "airflow": ["prefect", "dagster", "data pipeline"],
    # .NET Ecosystem Equivalents
    "asp.net": ["asp.net core", ".net", "c#", "entity framework", "web api", "mvc"],
    "asp.net core": ["asp.net", ".net core", ".net", "c#", "entity framework", "web api"],
    ".net": ["asp.net", "asp.net core", ".net core", "c#", ".net 8"],
    ".net core": [".net", "asp.net core", "c#", ".net 8"],
    "razor pages": ["asp.net", "asp.net core", "mvc", "react", "frontend"],
    "entity framework": ["ef core", "orm", "linq", "sql server", "sql"],
    # Reporting & BI Equivalents
    "power bi": ["tableau", "data visualization", "reporting", "dashboards", "sql"],
    "tableau": ["power bi", "data visualization", "reporting", "dashboards", "sql"],
    "data modeling": ["database design", "schema design", "relational database", "entity framework", "sql"],
    "data dictionary": ["data modeling", "schema design", "database documentation", "metadata"],
    "systems analysis": ["system design", "requirements gathering", "software engineering", "architecture"],
    # AI Engineering Equivalents
    "llm": ["generative ai", "nlp", "transformers", "openai", "anthropic"],
    "generative ai": ["llm", "nlp", "transformers", "openai", "anthropic"],
    "rag": ["vector database", "embeddings", "langchain", "llamaindex"],
    "vector database": ["pinecone", "milvus", "weaviate", "chromadb", "faiss"],
    "langchain": ["llamaindex", "haystack", "agentic workflows"],
    "cursor": ["claude code", "github copilot", "ai-assisted development"],
    "claude code": ["cursor", "github copilot", "ai-assisted development"],
}

HIGH_RISK_DIRECT_SUBSTITUTIONS = {
    "c",
    "c++",
    "kubernetes",
    "terraform",
    "embedded",
    "memory management",
    "pointers",
}


def has_term(text: str, term: str) -> bool:
    return keyword_pattern(term).search(text) is not None


def score_keywords(
    job_keywords: list[KeywordItem],
    resume_text: str,
    *,
    target_threshold: int = 75,
    rewrite_mode: str = "transferable",
    confirmed_skills: list[str] | None = None,
) -> ScoreResponse:
    confirmed = {normalize(skill) for skill in (confirmed_skills or [])}
    resume_normalized = normalize(resume_text)
    total_weight = sum(item.weight for item in job_keywords) or 1.0
    earned = 0.0
    matched: list[KeywordMatch] = []
    missing: list[KeywordMatch] = []
    unsupported: list[KeywordMatch] = []
    warnings: list[str] = []

    for item in job_keywords:
        exact = has_term(resume_normalized, item.term)
        confirmed_exact = item.term in confirmed
        if exact or confirmed_exact:
            earned += item.weight
            matched.append(
                KeywordMatch(
                    term=item.term,
                    category=item.category,
                    weight=item.weight,
                    status="exact",
                    evidence="Present in resume or confirmed skill profile.",
                    risk="low",
                )
            )
            continue

        equivalents = EQUIVALENTS.get(item.term, [])
        equivalent_hits = [
            term
            for term in equivalents
            if has_term(resume_normalized, term) or term in confirmed
        ]
        if equivalent_hits and rewrite_mode in {
            "transferable",
            "user_verified",
            "aggressive",
        }:
            risk = "high" if item.term in HIGH_RISK_DIRECT_SUBSTITUTIONS else "medium"
            credit = 0.35 if risk == "high" else 0.6
            if rewrite_mode == "user_verified" and item.term in confirmed:
                credit = 1.0
                risk = "low"
            elif rewrite_mode == "aggressive" and risk != "high":
                credit = 0.75
            earned += item.weight * credit
            matched.append(
                KeywordMatch(
                    term=item.term,
                    category=item.category,
                    weight=item.weight,
                    status="transferable",
                    evidence=f"Related evidence found: {', '.join(equivalent_hits)}.",
                    risk=risk,
                )
            )
            if risk == "high":
                unsupported.append(
                    KeywordMatch(
                        term=item.term,
                        category=item.category,
                        weight=item.weight,
                        status="unsupported",
                        evidence="High-risk direct substitution; use transferable wording unless you confirm real experience.",
                        risk="high",
                    )
                )
            continue

        keyword_match = KeywordMatch(
            term=item.term,
            category=item.category,
            weight=item.weight,
            status="missing",
            evidence=None,
            risk="high" if item.term in HIGH_RISK_DIRECT_SUBSTITUTIONS else "medium",
        )
        missing.append(keyword_match)
        if item.required or item.term in HIGH_RISK_DIRECT_SUBSTITUTIONS:
            unsupported.append(
                KeywordMatch(
                    term=item.term,
                    category=item.category,
                    weight=item.weight,
                    status="unsupported",
                    evidence="No direct or transferable evidence found in resume text.",
                    risk=keyword_match.risk,
                )
            )

    score = round((earned / total_weight) * 100, 2)
    if any(
        match.term in {"c", "c++"} and match.status != "exact"
        for match in matched + missing
    ):
        warnings.append(
            "C/C++ requirements are treated as high-risk substitutions. Prefer systems-concept wording unless you have real C/C++ experience."
        )
    if score < target_threshold:
        warnings.append(
            f"Keyword match is below target threshold of {target_threshold}%."
        )

    return ScoreResponse(
        match_score=score,
        target_met=score >= target_threshold,
        matched_keywords=matched,
        missing_keywords=missing,
        unsupported_keywords=unsupported,
        warnings=warnings,
    )
