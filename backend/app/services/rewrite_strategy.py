"""Pre-compute rewrite targeting before the LLM call."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .keyword_extractor import extract_keywords
from .latex import latex_to_text

TARGET_ROLE_IDENTITIES = (
    "backend_engineer",
    "frontend_engineer",
    "fullstack_engineer",
    "ai_platform_engineer",
    "cloud_engineer",
    "devops_engineer",
    "ml_engineer",
)

# Job-description signals per primary identity (regex, weight)
IDENTITY_JD_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "backend_engineer": [
        (r"\bbackend\b", 4),
        (r"\brest api\b", 3),
        (r"\bmicroservices\b", 3),
        (r"\bspring boot\b", 3),
        (r"\bapi design\b", 2),
        (r"\bdistributed systems\b", 3),
        (r"\bcaching\b", 2),
        (r"\bpostgresql\b", 2),
        (r"\bredis\b", 2),
        (r"\bscalability\b", 2),
    ],
    "frontend_engineer": [
        (r"\bfrontend\b", 4),
        (r"\breact\b", 3),
        (r"\btypescript\b", 3),
        (r"\bnext\.?js\b", 3),
        (r"\bui\b", 2),
        (r"\baccessibility\b", 2),
        (r"\bcomponent\b", 2),
        (r"\brendering\b", 2),
        (r"\bcss\b", 2),
    ],
    "fullstack_engineer": [
        (r"\bfull[\s-]?stack\b", 5),
        (r"\bend[\s-]to[\s-]end\b", 2),
        (r"\bfrontend\b", 2),
        (r"\bbackend\b", 2),
    ],
    "ai_platform_engineer": [
        (r"\bllm\b", 3),
        (r"\brag\b", 3),
        (r"\blangchain\b", 3),
        (r"\binference\b", 3),
        (r"\bmodel serving\b", 3),
        (r"\bai platform\b", 4),
        (r"\bprompt\b", 2),
        (r"\bevaluation\b", 2),
        (r"\bgpu\b", 2),
        (r"\borchestration\b", 2),
    ],
    "cloud_engineer": [
        (r"\bcloud engineer\b", 5),
        (r"\baws\b", 2),
        (r"\bazure\b", 2),
        (r"\bgcp\b", 2),
        (r"\bcloud architecture\b", 3),
        (r"\binfrastructure as code\b", 2),
        (r"\bterraform\b", 2),
    ],
    "devops_engineer": [
        (r"\bdevops\b", 4),
        (r"\bci/cd\b", 3),
        (r"\bkubernetes\b", 3),
        (r"\bdocker\b", 2),
        (r"\bhelm\b", 2),
        (r"\bobservability\b", 2),
        (r"\bsre\b", 3),
        (r"\bplatform reliability\b", 2),
    ],
    "ml_engineer": [
        (r"\bmachine learning\b", 4),
        (r"\bml engineer\b", 5),
        (r"\bdeep learning\b", 3),
        (r"\bpytorch\b", 3),
        (r"\bmodel training\b", 3),
        (r"\brecommendation\b", 2),
        (r"\bxgboost\b", 2),
        (r"\bfeature engineering\b", 2),
    ],
}

IDENTITY_GUIDANCE: dict[str, dict[str, str]] = {
    "backend_engineer": {
        "prioritize": "APIs, scalability, distributed systems, databases, caching, testing, reliability, backend architecture, and production systems",
        "de_emphasize": "prompt engineering, experimental AI terminology, pure UI styling, academic research phrasing",
        "emphasis": "Prioritize APIs, scalability, distributed systems, databases, caching, testing, reliability, backend architecture, and production systems.",
    },
    "frontend_engineer": {
        "prioritize": "React, TypeScript, UI architecture, performance optimization, accessibility, rendering, and component systems",
        "de_emphasize": "backend-only infrastructure depth, ML training pipelines, DevOps tooling unless job requires them",
        "emphasis": "Prioritize React, TypeScript, UI architecture, performance optimization, accessibility, rendering, and component systems.",
    },
    "fullstack_engineer": {
        "prioritize": "end-to-end product delivery, React/TypeScript frontends, backend APIs, databases, and integration across the stack",
        "de_emphasize": "narrow specialization in only ML research or only low-level infra unless supported",
        "emphasis": "Balance frontend and backend accomplishments with integrated delivery stories.",
    },
    "ai_platform_engineer": {
        "prioritize": "inference systems, LLM integration, orchestration, evaluation pipelines, observability, deployment, GPU infrastructure, and scalable AI workflows",
        "de_emphasize": "generic CRUD backend work unrelated to AI systems, excessive frontend UI detail",
        "emphasis": "Prioritize inference systems, LLM integration, orchestration, evaluation pipelines, observability, deployment, GPU infrastructure, and scalable AI workflows.",
    },
    "cloud_engineer": {
        "prioritize": "cloud architecture, AWS/Azure/GCP services, networking, security, IaC, cost optimization, and highly available deployments",
        "de_emphasize": "application-level UI details, academic ML experimentation",
        "emphasis": "Prioritize cloud architecture, managed services, IaC, security, and production reliability.",
    },
    "devops_engineer": {
        "prioritize": "CI/CD, Kubernetes, Docker, Terraform, monitoring, SLOs, deployment automation, and platform reliability",
        "de_emphasize": "product UI features, business-domain analytics unless relevant",
        "emphasis": "Prioritize CI/CD, Kubernetes, observability, deployment automation, and platform reliability.",
    },
    "ml_engineer": {
        "prioritize": "model training, feature engineering, evaluation metrics, data pipelines, inference optimization, and production ML systems",
        "de_emphasize": "generic web UI work, prompt-registry product details unless job-relevant",
        "emphasis": "Prioritize model training, evaluation, data pipelines, and production ML delivery.",
    },
}

# Map legacy role_category from job_analyzer to default identity when JD is ambiguous
LEGACY_ROLE_DEFAULT_IDENTITY = {
    "AI Engineer": "ai_platform_engineer",
    "AI Support": "devops_engineer",
    "ML Engineer": "ml_engineer",
    "Software Engineer": "fullstack_engineer",
}

EMPLOYER_PATTERNS = [
    (r"cognizant", "Cognizant"),
    (r"university of south florida|\busf\b", "University of South Florida"),
    (r"exposys", "Exposys Data Labs"),
]

SOFTWARE_ENGINEERING_IDENTITIES = frozenset(
    {
        "backend_engineer",
        "frontend_engineer",
        "fullstack_engineer",
        "cloud_engineer",
        "devops_engineer",
    }
)


@dataclass
class RewriteStrategy:
    target_role: str
    top_skills: list[str] = field(default_factory=list)
    priority_experiences: list[str] = field(default_factory=list)
    priority_projects: list[str] = field(default_factory=list)
    prioritize: str = ""
    de_emphasize: str = ""
    identity_emphasis: str = ""

    def to_prompt_block(self) -> str:
        return f"""TARGET ROLE CLASSIFICATION:
{self.target_role}

TOP PRIORITY TECHNOLOGIES:
{", ".join(self.top_skills) if self.top_skills else "Infer from job description using only resume-supported skills"}

PRIORITY EXPERIENCES TO STRENGTHEN FIRST:
{", ".join(self.priority_experiences) if self.priority_experiences else "Most relevant roles inferred from job match"}

PRIORITY PROJECTS TO EMPHASIZE:
{", ".join(self.priority_projects) if self.priority_projects else "Most relevant project themes from templates"}

PRIORITIZE:
{self.prioritize}

DE-EMPHASIZE:
{self.de_emphasize}

ROLE IDENTITY LOCK:
- Maintain ONE dominant professional identity ({self.target_role}) across emphasized bullets, skills ordering, and project framing.
- Do NOT blend unrelated identities (e.g., AI researcher + frontend engineer + DevOps architect) unless all are explicitly supported in the original resume.
- {self.identity_emphasis}
"""


def _score_identity(job_lower: str, patterns: list[tuple[str, int]]) -> int:
    return sum(weight * len(re.findall(pat, job_lower)) for pat, weight in patterns)


def classify_target_role_identity(
    job_description: str,
    resume_text: str,
    effective_role_category: str,
) -> str:
    from .project_framing import JAVA_JD

    job_lower = job_description.lower()

    # Java/Spring JD always wins over UI-selected "AI Engineer" or resume AI keywords
    if JAVA_JD.search(job_description):
        return "backend_engineer"

    scores = {
        identity: _score_identity(job_lower, patterns)
        for identity, patterns in IDENTITY_JD_KEYWORDS.items()
    }

    backend = scores["backend_engineer"]
    frontend = scores["frontend_engineer"]
    fullstack = scores["fullstack_engineer"]

    best_identity = max(scores, key=lambda k: scores[k])
    best_score = scores[best_identity]

    if best_score == 0:
        return LEGACY_ROLE_DEFAULT_IDENTITY.get(
            effective_role_category, "fullstack_engineer"
        )

    if backend >= 3 and frontend >= 3 and fullstack >= 2:
        return "fullstack_engineer"

    # Prefer JD signal over stale UI role category (e.g. AI Engineer selected from prior analysis)
    if backend >= 4 and best_identity == "backend_engineer":
        return "backend_engineer"
    if frontend >= 4 and best_identity == "frontend_engineer":
        return "frontend_engineer"

    legacy_default = LEGACY_ROLE_DEFAULT_IDENTITY.get(effective_role_category)
    if (
        legacy_default
        and scores.get(legacy_default, 0) >= best_score - 2
        and legacy_default == best_identity
    ):
        return legacy_default

    return best_identity


def _extract_resume_skills(resume_text: str, job_description: str, limit: int = 8) -> list[str]:
    job_keywords = extract_keywords(job_description, job_context=True)
    resume_lower = resume_text.lower()
    ranked: list[tuple[int, str]] = []

    for kw in job_keywords:
        term = kw.term.strip()
        if len(term) < 2:
            continue
        if term.lower() not in resume_lower:
            continue
        job_count = len(
            re.findall(rf"\b{re.escape(term.lower())}\b", job_description.lower())
        )
        ranked.append((job_count * int(kw.weight), term))

    ranked.sort(key=lambda x: x[0], reverse=True)
    seen: set[str] = set()
    skills: list[str] = []
    for _, term in ranked:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        skills.append(term)
        if len(skills) >= limit:
            break
    return skills


def _extract_priority_experiences(resume_text: str, job_description: str) -> list[str]:
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()
    found: list[tuple[int, str]] = []

    for pattern, label in EMPLOYER_PATTERNS:
        if re.search(pattern, resume_lower):
            relevance = 1
            if "cognizant" in label.lower() and any(
                t in job_lower
                for t in ("java", "spring", "backend", "api", "microservice")
            ):
                relevance += 3
            if "south florida" in label.lower() and any(
                t in job_lower for t in ("react", "typescript", "llm", "ai", "full stack", "fullstack")
            ):
                relevance += 3
            found.append((relevance, label))

    # Thematic tags from JD + resume overlap
    themes = []
    theme_rules = [
        (r"\brest api\b|\bbackend\b|\bspring\b", "Backend APIs"),
        (r"\breact\b|\bfrontend\b|\btypescript\b", "Frontend development"),
        (r"\bllm\b|\brag\b|\bai\b", "AI platform work"),
        (r"\bdocker\b|\bkubernetes\b|\bci/cd\b", "Infrastructure and DevOps"),
    ]
    for pattern, theme in theme_rules:
        if re.search(pattern, job_lower) and re.search(pattern, resume_lower):
            themes.append(theme)

    employers = [label for _, label in sorted(found, key=lambda x: x[0], reverse=True)]
    combined = employers + [t for t in themes if t not in employers]
    return combined[:5]


def _extract_priority_projects(
    selected_projects: list[dict],
    target_role: str,
) -> list[str]:
    labels = []
    for project in selected_projects[:2]:
        title = project.get("title") or project.get("name", "")
        short = title.split(" - ")[0].strip()
        if len(short) > 60:
            short = short[:57] + "..."
        labels.append(short)

    if target_role in ("backend_engineer", "devops_engineer", "cloud_engineer"):
        labels.append("Distributed systems and infrastructure")
    if target_role == "ai_platform_engineer":
        labels.append("LLM platform and inference")
    if target_role == "ml_engineer":
        labels.append("ML pipelines and model serving")

    seen: set[str] = set()
    unique: list[str] = []
    for label in labels:
        if label and label not in seen:
            seen.add(label)
            unique.append(label)
    return unique[:4]


def build_rewrite_strategy(
    job_description: str,
    resume_latex: str,
    effective_role_category: str,
    selected_projects: list[dict],
    missing_terms: list[str] | None = None,
) -> RewriteStrategy:
    resume_text = latex_to_text(resume_latex)
    target_role = classify_target_role_identity(
        job_description, resume_text, effective_role_category
    )
    guidance = IDENTITY_GUIDANCE[target_role]

    top_skills = _extract_resume_skills(resume_text, job_description)
    if missing_terms:
        for term in missing_terms[:3]:
            if term not in top_skills:
                top_skills.append(term)
        top_skills = top_skills[:8]

    return RewriteStrategy(
        target_role=target_role,
        top_skills=top_skills,
        priority_experiences=_extract_priority_experiences(resume_text, job_description),
        priority_projects=_extract_priority_projects(selected_projects, target_role),
        prioritize=guidance["prioritize"],
        de_emphasize=guidance["de_emphasize"],
        identity_emphasis=guidance["emphasis"],
    )


def is_software_engineering_identity(target_role: str) -> bool:
    return target_role in SOFTWARE_ENGINEERING_IDENTITIES or target_role == "fullstack_engineer"
