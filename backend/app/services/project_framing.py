"""Role-specific project reframing and identity-aware project selection."""

from __future__ import annotations

import re
from copy import deepcopy

from .projects_data import PROJECTS

# Which project IDs are eligible per target identity
IDENTITY_PROJECT_POOL: dict[str, list[int]] = {
    "ai_platform_engineer": [1, 2, 3],
    "ml_engineer": [1, 2],
    "backend_engineer": [3, 2, 1],
    "frontend_engineer": [2, 1],
    "fullstack_engineer": [3, 2, 1],
    "devops_engineer": [2, 1],
    "cloud_engineer": [2, 1],
}

# Legacy role_category → default identity when identity not passed
LEGACY_CATEGORY_POOL: dict[str, list[int]] = {
    "AI Engineer": [1, 2],
    "AI Support": [1, 2],
    "ML Engineer": [1, 2],
    "Software Engineer": [3, 2, 1],
    "Java Developer": [3, 2, 1],
}

AI_HEAVY_TERMS = re.compile(
    r"\b(langgraph|langchain|llm|rag|prompt|multi-agent|agentic|token|gemini|openai|vector)\b",
    re.IGNORECASE,
)

BACKEND_TERMS = re.compile(
    r"\b(java|spring boot|spring framework|spring\b|rest api|restful|sql|jdbc|"
    r"oop|collections|exception handling|hibernate|jsp|servlet|j2ee|core java|"
    r"junit|debugging|web application)\b",
    re.IGNORECASE,
)

JAVA_JD = re.compile(
    r"\b(java developer|java development|core java|spring boot|spring framework|j2ee|"
    r"developer\s*\(\s*java\s*\)|software developer[^\n]{0,60}\bjava\b)\b",
    re.IGNORECASE,
)

INDUSTRY_DOMAIN_CONTEXT: dict[str, str] = {
    "Fintech": "banking, payments, and fraud-prevention workflows",
    "Healthcare": "clinical data and patient-facing workflows",
    "Cybersecurity": "identity, access-control, and threat-detection workflows",
    "Education": "student, instructor, and learning-analytics workflows",
    "E-commerce": "catalog, checkout, and customer-engagement workflows",
}

JD_DOMAIN_PATTERNS: list[tuple[str, str]] = [
    (r"\b(payment|payments|banking|transaction|transactions|ledger|fraud|fintech)\b", INDUSTRY_DOMAIN_CONTEXT["Fintech"]),
    (r"\b(patient|clinical|medical|healthcare|hipaa|ehr|claims)\b", INDUSTRY_DOMAIN_CONTEXT["Healthcare"]),
    (r"\b(security|cybersecurity|identity|authentication|authorization|threat|iam)\b", INDUSTRY_DOMAIN_CONTEXT["Cybersecurity"]),
    (r"\b(student|instructor|education|learning|course|classroom|edtech)\b", INDUSTRY_DOMAIN_CONTEXT["Education"]),
    (r"\b(ecommerce|e-commerce|retail|checkout|catalog|order|orders|cart)\b", INDUSTRY_DOMAIN_CONTEXT["E-commerce"]),
]

OUTCOME_CLAUSE = re.compile(
    r",\s+(reducing|improving|enabling|supporting|maintaining|cutting|achieving|"
    r"lowering|surfacing|increasing|flagging|ensuring|reaching)\b",
    re.IGNORECASE,
)

JD_TECH_PHRASES: list[tuple[str, str, tuple[str, ...]]] = [
    (r"\bmicroservices?\b", "microservices", ("REST APIs", "FastAPI", "Spring Boot", "Node.js")),
    (r"\brest(?:ful)? api(s)?\b|\bapi design\b", "REST API design", ("REST APIs", "FastAPI", "Spring Boot", "Node.js")),
    (r"\bspring boot\b|\bcore java\b", "Java/Spring Boot", ("Java", "Spring Boot")),
    (r"\breact\b|\btypescript\b|\bfront[\s-]?end\b", "React/TypeScript", ("React", "TypeScript", "Next.js")),
    (r"\bpostgresql\b|\bsql\b|\brelational database\b", "relational data modeling", ("PostgreSQL", "SQL Server", "SQL")),
    (r"\bredis\b|\bcach(e|ing)\b", "Redis caching", ("Redis",)),
    (r"\bdocker\b|\bkubernetes\b|\bci/cd\b|\bdevops\b", "containerized deployment", ("Docker", "Kubernetes", "GitHub Actions")),
    (r"\bjunit\b|\btesting\b|\btest coverage\b", "automated testing", ("JUnit", "Jest", "Cucumber")),
]


def materialize_project_for_identity(project: dict, target_role_identity: str) -> dict:
    """Apply role-specific title, bullets, and tech stack when framing exists."""
    out = deepcopy(project)
    framing = project.get("framing") or {}
    variant = framing.get(target_role_identity)
    if not variant:
        return out
    out["title"] = variant.get("title", out["title"])
    out["bullets"] = list(variant.get("bullets", out["bullets"]))
    if variant.get("tech_stack"):
        out["tech_stack"] = list(variant["tech_stack"])
    out["applied_framing"] = target_role_identity
    return out


def _score_project_for_jd(project: dict, job_description: str) -> float:
    score = 0.0
    for tech in project.get("tech_stack", []):
        pattern = re.compile(rf"\b{re.escape(tech.lower())}\b", re.IGNORECASE)
        score += len(pattern.findall(job_description)) * 2.0
    desc = f"{project.get('title', '')} {project.get('description', '')}"
    for word in set(re.findall(r"\b\w{3,}\b", desc.lower())):
        if word in {
            "system", "platform", "production", "framework", "real", "time",
            "using", "with", "and", "the", "for", "are", "our", "out", "can", "has", "its",
        }:
            continue
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        score += len(pattern.findall(job_description))
    return score


def _derive_domain_context(job_description: str, effective_industry: str | None) -> str | None:
    for pattern, context in JD_DOMAIN_PATTERNS:
        if re.search(pattern, job_description, re.IGNORECASE):
            return context
    if effective_industry:
        return INDUSTRY_DOMAIN_CONTEXT.get(effective_industry)
    return None


def _insert_domain_context(bullet: str, domain_context: str | None) -> str:
    if not domain_context:
        return bullet
    domain_terms = [
        term
        for term in re.findall(r"\b[a-z][a-z-]{3,}\b", domain_context.lower())
        if term not in {"workflows", "data", "and"}
    ]
    if any(term in bullet.lower() for term in domain_terms):
        return bullet

    stripped = bullet.rstrip(".")
    match = OUTCOME_CLAUSE.search(stripped)
    if match:
        return f"{stripped[:match.start()]} for {domain_context}{stripped[match.start():]}."
    return f"{stripped} for {domain_context}."


def _supported_jd_phrases(project: dict, job_description: str) -> list[str]:
    stack_text = " ".join(project.get("tech_stack", [])).lower()
    phrases: list[str] = []
    for pattern, phrase, supported_by in JD_TECH_PHRASES:
        if not re.search(pattern, job_description, re.IGNORECASE):
            continue
        if any(term.lower() in stack_text for term in supported_by):
            phrases.append(phrase)
    return phrases[:3]


def _add_jd_focus_to_bullet(bullet: str, phrases: list[str]) -> str:
    missing = [phrase for phrase in phrases if phrase.lower() not in bullet.lower()]
    if not missing:
        return bullet
    focus = ", ".join(missing[:2])
    stripped = bullet.rstrip(".")
    match = OUTCOME_CLAUSE.search(stripped)
    if match:
        return f"{stripped[:match.start()]} with {focus}{stripped[match.start():]}."
    return f"{stripped} with {focus}."


def adapt_projects_to_job_description(
    projects: list[dict],
    job_description: str,
    effective_industry: str | None,
    target_role_identity: str,
) -> list[dict]:
    """Lightly tailor selected project templates to explicit JD domain and stack signals."""
    domain_context = _derive_domain_context(job_description, effective_industry)
    adapted: list[dict] = []

    for index, project in enumerate(projects):
        out = deepcopy(project)
        phrases = _supported_jd_phrases(out, job_description)
        bullets = list(out.get("bullets", []))
        if bullets:
            bullets[0] = _insert_domain_context(bullets[0], domain_context)
            if phrases:
                target_index = 1 if len(bullets) > 1 else 0
                bullets[target_index] = _add_jd_focus_to_bullet(bullets[target_index], phrases)

        out["bullets"] = bullets
        if domain_context:
            out["jd_domain_context"] = domain_context
        if phrases:
            out["jd_focus_phrases"] = phrases
        out["applied_framing"] = out.get("applied_framing", target_role_identity)
        adapted.append(out)

    return adapted


def infer_identity_from_jd(role_category: str, job_description: str) -> str:
    """Lightweight identity guess when caller did not provide one."""
    if role_category == "AI Engineer":
        return "ai_platform_engineer"
    if role_category == "ML Engineer":
        return "ml_engineer"
    if role_category in ("AI Support",):
        return "devops_engineer"
    if BACKEND_TERMS.search(job_description) and not (
        AI_HEAVY_TERMS.search(job_description) and "rag" in job_description.lower()
    ):
        return "backend_engineer"
    if AI_HEAVY_TERMS.search(job_description):
        return "ai_platform_engineer"
    return "fullstack_engineer"


def select_projects(
    role_category: str,
    job_description: str,
    target_role_identity: str | None = None,
) -> list[dict]:
    """
    Pick two projects from the pool for the target identity, score by JD fit,
    then apply role-specific reframing.
    """
    if not target_role_identity:
        target_role_identity = infer_identity_from_jd(role_category, job_description)

    pool_ids = IDENTITY_PROJECT_POOL.get(target_role_identity or "")
    if not pool_ids:
        pool_ids = LEGACY_CATEGORY_POOL.get(role_category, [5, 7, 8, 9])

    pool = [p for p in PROJECTS if p["id"] in pool_ids]
    if not pool:
        pool = list(PROJECTS)

    identity = target_role_identity or "fullstack_engineer"
    scored = [
        (_score_project_for_jd(materialize_project_for_identity(p, identity), job_description), p)
        for p in pool
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Java-focused JD: always include the Java/Spring project when available.
    if target_role_identity in ("backend_engineer", "fullstack_engineer") and JAVA_JD.search(job_description):
        java_project = next((p for p in pool if p["id"] == 3), None)
        if java_project:
            others = sorted(
                [(s, p) for s, p in scored if p["id"] != 3],
                key=lambda x: x[0],
                reverse=True,
            )
            top_two = [java_project]
            if others:
                top_two.append(others[0][1])
            return [materialize_project_for_identity(p, identity) for p in top_two[:2]]

    # Backend/Java JD: prioritize backend-framed projects
    if target_role_identity == "backend_engineer" and BACKEND_TERMS.search(job_description):
        non_ai = [(s, p) for s, p in scored if p["id"] == 3 or p["id"] == 2]
        if len(non_ai) >= 2:
            scored = non_ai

    top_two = [p for _, p in scored[:2]]
    return [materialize_project_for_identity(p, identity) for p in top_two]


def build_project_reframing_instructions(target_role_identity: str) -> str:
    """Prompt block for selective emphasis and anti-hallucination on projects/skills."""
    compress_ai = target_role_identity in {
        "backend_engineer",
        "frontend_engineer",
        "fullstack_engineer",
    }
    blocks = [
        "ROLE-SPECIFIC PROJECT REFRAMING (MANDATORY):",
        f"- Primary identity: {target_role_identity}. Present both projects through this lens.",
        "- Use the provided project titles and bullets as the source of truth for scope and metrics.",
        "- Do NOT use AI-centric titles (multi-agent, prompt registry, LangGraph, token tracing) unless identity is ai_platform_engineer or ml_engineer.",
    ]
    if compress_ai:
        blocks.extend([
            "- DE-EMPHASIZE: LangGraph, multi-agent orchestration, prompt experimentation, LLM token tracing, autonomous agents.",
            "- EMPHASIZE: REST APIs, databases, caching, reliability, web application architecture, debugging, production backend patterns.",
            "- Reframe AI work as engineering outcomes (latency, concurrency, data integrity) not research narratives.",
        ])
    if target_role_identity == "backend_engineer":
        blocks.append(
            "- Example title shift: 'Autonomous Multi-Agent Platform' → 'Distributed Workflow Execution API' (same work, backend identity)."
        )
    if target_role_identity == "fullstack_engineer":
        blocks.append(
            "- Example title shift: emphasize end-to-end web delivery (React/TypeScript UI + API + database), not agent frameworks."
        )
    return "\n".join(blocks)


def extract_jd_foundational_concepts(job_description: str) -> list[str]:
    """Concepts explicitly named in JD (OOP, Collections, etc.) to surface in experience bullets."""
    jd = job_description.lower()
    concepts: list[tuple[str, str]] = [
        (r"\boop\b|\bobject[- ]oriented\b", "OOP"),
        (r"\bcollections\b", "Java Collections"),
        (r"\bexception handling\b", "exception handling"),
        (r"\bcore java\b", "Core Java"),
        (r"\bdata structures\b", "data structures"),
        (r"\balgorithms\b", "algorithms"),
        (r"\bmultithreading\b|\bconcurrency\b", "concurrency"),
        (r"\bdebugging\b", "debugging"),
        (r"\brelational database\b|\bsql\b", "SQL"),
    ]
    found: list[str] = []
    for pattern, label in concepts:
        if re.search(pattern, jd, re.IGNORECASE):
            found.append(label)
    return found


def extract_resume_supported_terms(resume_text: str) -> set[str]:
    """Terms explicitly present in resume — skills section must not add vendors/tools outside this set unless in confirmed_skills."""
    text = resume_text.lower()
    catalog = [
        "java", "spring boot", "spring", "typescript", "javascript", "python", "node.js",
        "react", "next.js", "fastapi", "postgresql", "mongodb", "redis", "sql server",
        "oracle", "aws", "docker", "jenkins", "github actions", "kubernetes", "terraform",
        "prometheus", "grafana", "junit", "cucumber", "jest", "langchain", "groq",
        "express", "html", "css", "sql", "microservices", "rest api", "hibernate",
        "kafka", "jsp", "servlet",
    ]
    supported: set[str] = set()
    for term in catalog:
        if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
            supported.add(term)
    return supported


def build_selective_emphasis_instructions(
    target_role_identity: str,
    priority_experiences: list[str],
) -> str:
    lines = [
        "SELECTIVE REWRITE WEIGHT (not equal weight across sections):",
    ]
    if target_role_identity == "backend_engineer":
        lines.extend([
            "- EXPAND: Cognizant (or other backend/API employers) — strongest Java/Spring/SQL/API bullets, 4–6 bullets worth of detail.",
            "- COMPRESS: USF/research roles — fewer bullets; frame as backend services (APIs, PostgreSQL, concurrency) not AI research.",
            "- COMPRESS: Projects section — 2–3 tight bullets per project; backend/web identity only.",
        ])
    elif target_role_identity == "fullstack_engineer":
        lines.extend([
            "- EXPAND: roles showing React/TypeScript + backend APIs.",
            "- BALANCE: one project API-heavy, one project UI+API integration.",
        ])
    elif target_role_identity in ("ai_platform_engineer", "ml_engineer"):
        lines.extend([
            "- EXPAND: AI/ML projects and platform bullets.",
            "- Keep agent/LLM terminology where supported by resume.",
        ])
    else:
        lines.append("- Balance experience and projects evenly unless job description strongly favors one area.")

    if priority_experiences:
        lines.append(f"- Prioritize strengthening: {', '.join(priority_experiences[:4])}.")
    return "\n".join(lines)


def build_evidence_linked_skills_instructions(
    supported_terms: set[str],
    missing_terms: list[str],
    confirmed_skills: list[str],
) -> str:
    supported_sample = ", ".join(sorted(supported_terms)[:25]) or "see original resume"
    confirmed = ", ".join(confirmed_skills) if confirmed_skills else "none"
    return f"""EVIDENCE-LINKED SKILLS (MANDATORY):
- Resume-supported technologies (may appear in Skills or bullets): {supported_sample}
- User-confirmed skills (may add): {confirmed}
- Do NOT add specific vendors or tools not in the supported list above unless listed in user-confirmed skills.
  Example: do NOT add Oracle, Hibernate, Kafka, JSP, or Spring Security unless they appear in the original resume or confirmed skills.
- For missing JD terms that are adjacent (e.g., Oracle when only PostgreSQL/SQL Server appear), use generic phrasing: "relational databases (PostgreSQL, SQL Server)" — not the unsupported vendor name.
- Missing JD terms to address only when supported or transferable: {", ".join(missing_terms[:12]) or "none"}
"""


def build_stack_experience_framing_instructions(target_stack: str) -> str:
    """
    Constructs prompt instructions for Cognizant Java guardrail and USF stack adaptation.
    target_stack is one of: 'dotnet', 'java', 'node', 'python', 'ai'.
    """
    stack = target_stack.lower().strip()

    if stack in ("dotnet", ".net", "c#", "csharp"):
        cognizant_guard = (
            "COGNIZANT EXPERIENCE (.NET / C# TARGET STACK):\n"
            "- Adapt Cognizant Technology Solutions to C# / .NET, ASP.NET Core, Entity Framework Core, SQL Server, and REST APIs.\n"
        )
        usf_framing = (
            "USF EXPERIENCE & PROJECTS ADAPTATION (.NET TARGET STACK):\n"
            "- USF and Projects MUST STAY Python (Python, FastAPI, React, multi-agent workflows).\n"
            "- Do NOT rewrite USF or projects into .NET/C#.\n"
        )
    elif stack == "java":
        cognizant_guard = (
            "COGNIZANT EXPERIENCE GUARDRAIL (STRICT MANDATORY):\n"
            "- Do NOT change the backend language or core technology stack of the Cognizant work experience entry.\n"
            "- Cognizant MUST remain Java-focused (Java, Spring Boot, REST APIs, PostgreSQL/SQL, Microservices).\n"
            "- You may reword Cognizant bullets for metric impact, action verbs, and scale, but NEVER replace Java with Node.js or Python.\n"
            "- Defensibility limits: Focus Cognizant on Java/Spring microservices, Redis caching, SQL/MongoDB, and testing; do NOT inject payment webhooks (Stripe), cloud autoscaling infra, or RabbitMQ into Cognizant.\n"
        )
        usf_framing = (
            "USF EXPERIENCE & PROJECTS ADAPTATION (JAVA TARGET STACK):\n"
            "- USF and Projects MUST STAY Python (Python, FastAPI, React, multi-agent workflows).\n"
            "- Do NOT rewrite USF or projects into Java.\n"
        )
    elif stack in ("node", "node.js", "fullstack"):
        cognizant_guard = (
            "COGNIZANT EXPERIENCE GUARDRAIL (STRICT MANDATORY):\n"
            "- Do NOT change the backend language or core technology stack of the Cognizant work experience entry.\n"
            "- Cognizant MUST remain Java-focused (Java, Spring Boot, REST APIs, PostgreSQL/SQL, Microservices).\n"
            "- You may reword Cognizant bullets for metric impact, action verbs, and scale, but NEVER replace Java with Node.js or Python.\n"
            "- Defensibility limits: Focus Cognizant on Java/Spring microservices, Redis caching, SQL/MongoDB, and testing; do NOT inject payment webhooks (Stripe), cloud autoscaling infra, or RabbitMQ into Cognizant.\n"
        )
        usf_framing = (
            "USF EXPERIENCE & PROJECTS ADAPTATION (NODE.JS TARGET STACK):\n"
            "- Adapt USF (University of San Francisco) experience bullets to showcase Node.js, TypeScript, React, Express/Fastify, and fullstack web workflows.\n"
            "- Ensure Projects section features Node.js, TypeScript, React fullstack architectures.\n"
        )
    elif stack in ("ai", "ml", "ai_engineer", "ml_engineer"):
        cognizant_guard = (
            "COGNIZANT EXPERIENCE GUARDRAIL (STRICT MANDATORY):\n"
            "- Do NOT change the backend language or core technology stack of the Cognizant work experience entry.\n"
            "- Cognizant MUST remain Java-focused (Java, Spring Boot, REST APIs, PostgreSQL/SQL, Microservices).\n"
            "- You may reword Cognizant bullets for metric impact, action verbs, and scale, but NEVER replace Java with Node.js or Python.\n"
            "- Defensibility limits: Focus Cognizant on Java/Spring microservices, Redis caching, SQL/MongoDB, and testing; do NOT inject payment webhooks (Stripe), cloud autoscaling infra, or RabbitMQ into Cognizant.\n"
        )
        usf_framing = (
            "USF EXPERIENCE & PROJECTS ADAPTATION (AI TARGET STACK):\n"
            "- Adapt USF (University of San Francisco) experience bullets to showcase Python, LLMs, RAG, and AI agent workflows.\n"
            "- Ensure Projects section features Python / AI architectures.\n"
        )
    else:  # python
        cognizant_guard = (
            "COGNIZANT EXPERIENCE GUARDRAIL (STRICT MANDATORY):\n"
            "- Do NOT change the backend language or core technology stack of the Cognizant work experience entry.\n"
            "- Cognizant MUST remain Java-focused (Java, Spring Boot, REST APIs, PostgreSQL/SQL, Microservices).\n"
            "- You may reword Cognizant bullets for metric impact, action verbs, and scale, but NEVER replace Java with Node.js or Python.\n"
            "- Defensibility limits: Focus Cognizant on Java/Spring microservices, Redis caching, SQL/MongoDB, and testing; do NOT inject payment webhooks (Stripe), cloud autoscaling infra, or RabbitMQ into Cognizant.\n"
        )
        usf_framing = (
            "USF EXPERIENCE & PROJECTS ADAPTATION (PYTHON TARGET STACK):\n"
            "- Adapt USF (University of San Francisco) experience bullets to showcase Python, FastAPI, data pipelines, and backend/AI workflows.\n"
            "- Ensure Projects section features Python / FastAPI / data-driven architectures.\n"
        )

    return cognizant_guard + "\n" + usf_framing

