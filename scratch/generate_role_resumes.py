"""Generate role-tailored resume .tex files from resume.tex and projects_data.

Four SWE tracks + AI:
  - Java          → general Software Engineer (Java / Spring Boot roles)
  - Node/TS       → general Software Engineer (Node.js / TypeScript roles)
  - Python/TS     → general Software Engineer (Python / TypeScript roles)
  - AI Engineer   → AI / LLM platform roles
"""

from __future__ import annotations

import re
from pathlib import Path

from backend.app.services.latex_projects import replace_projects_section
from backend.app.services.project_framing import materialize_project_for_identity, select_projects
from backend.app.services.projects_data import PROJECTS

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "resume.tex").read_text(encoding="utf-8")
OUT = Path(__file__).resolve().parent

JAVA_JD = """
Software Engineer. Java, Spring Boot, REST APIs, PostgreSQL, Redis, OOP, microservices.
JUnit, Git, Agile, debugging.
""".strip()

NODE_JD = """
Software Engineer. React, TypeScript, Node.js, Express.js, REST APIs, PostgreSQL, Redis.
Docker, GitHub Actions, Agile.
""".strip()

PYTHON_JD = """
Software Engineer. Python, FastAPI, React, TypeScript, REST APIs, PostgreSQL, Redis.
Docker, GitHub Actions, Agile.
""".strip()

AI_JD = """
AI Engineer. LLM integration, RAG pipelines, LangChain, prompt engineering.
Model serving, evaluation, GPU inference. Python, FastAPI. Docker, Kubernetes.
""".strip()

# --- Experience blocks ---

JAVA_USF = r"""  \resumeSubheading
    {University of South Florida}{Graduate Researcher - Backend Software Engineer}{Jan 2025}{Present}
  \resumeItemListStart
    \resumeItem{Built backend services and a \textbf{PostgreSQL} persistence layer for a production biomedical learning platform used by USF SHIELD Lab, supporting authentication, enrollment, progress tracking, and role-based access across student, instructor, and researcher personas.}
    \resumeItem{Designed normalized \textbf{SQL} schemas and \textbf{REST APIs} for user registration, session management, and workflow state transitions, applying service-layer \textbf{OOP} abstractions and \textbf{exception-handling} patterns to keep business logic reusable across 13 application modules.}
    \resumeItem{Implemented input-validation and business-rule services with consistent error responses and typed request/response contracts, reducing frontend-backend integration defects by 30\% across sprint delivery cycles.}
    \resumeItem{Leveraged \textbf{Redis} for session and response caching on authentication and dashboard read paths, supporting 60+ concurrent classroom users with sub-2s p95 latency during peak usage.}
    \resumeItem{Integrated third-party HTTP APIs behind retry-aware service interfaces with timeout and fallback controls, isolating downstream failures from core registration and progress-tracking workflows.}
    \resumeItem{Delivered production releases on 2-week \textbf{Agile} sprint cycles using \textbf{Git}-based branching and peer code review, shipping 8+ major module updates without downtime for live classroom users.}
  \resumeItemListEnd"""

NODE_USF = r"""  \resumeSubheading
    {University of South Florida}{Graduate Researcher - Software Engineer}{Jan 2025}{Present}
  \resumeItemListStart
    \resumeItem{Architected and shipped a production web platform end-to-end, translating requirements from faculty and research stakeholders into 13 interactive modules built with \textbf{React} and \textbf{TypeScript}, serving students, instructors, and researchers at USF SHIELD Lab.}
    \resumeItem{Designed and implemented \textbf{Node.js} and \textbf{Express.js} backend services with \textbf{REST APIs} powering enrollment, progress tracking, AI-assisted learning workflows, authentication, and role-based access control, supporting 60+ concurrent users with sub-2s response latency.}
    \resumeItem{Designed \textbf{PostgreSQL} schemas and shared TypeScript contracts across frontend and backend services, reducing integration defects by 30\% and accelerating feature delivery across sprint cycles.}
    \resumeItem{Delivered adaptive student exercises and instructor curriculum tools with server-side validation, role-based routing, and production monitoring across multiple course workflows.}
    \resumeItem{Shipped 8+ major module updates on 2-week Agile iteration cycles using \textbf{Git}-based workflows, code reviews, and production monitoring without disrupting live classroom usage.}
  \resumeItemListEnd"""

PYTHON_USF = r"""  \resumeSubheading
    {University of South Florida}{Graduate Researcher - Software Engineer}{Jan 2025}{Present}
  \resumeItemListStart
    \resumeItem{Architected and shipped a production web platform end-to-end, translating requirements from faculty and research stakeholders into 13 interactive modules built with \textbf{React} and \textbf{TypeScript}, serving students, instructors, and researchers at USF SHIELD Lab.}
    \resumeItem{Built a \textbf{Python/Flask} REST API for AI-assisted learning workflows, integrating \textbf{Groq} and \textbf{Gemini} with task-based grading rubrics and response caching, supporting 60+ concurrent users with sub-2s response latency.}
    \resumeItem{Integrated \textbf{Supabase} (\textbf{PostgreSQL}) for authentication, enrollment, progress tracking, and quiz persistence across student, instructor, and researcher personas.}
    \resumeItem{Delivered adaptive student exercises and instructor curriculum tools with role-based routing and production monitoring across multiple course workflows.}
    \resumeItem{Shipped 8+ major module updates on 2-week Agile iteration cycles using \textbf{Git}-based workflows, code reviews, and production monitoring without disrupting live classroom usage.}
  \resumeItemListEnd"""

AI_USF = r"""  \resumeSubheading
    {University of South Florida}{Graduate Researcher - Full-Stack AI Platform}{Jan 2025}{Present}
  \resumeItemListStart
    \resumeItem{Took an AI-powered biomedical learning platform from concept to production at USF SHIELD Lab, owning product design, frontend, backend, database, and LLM integration for students and instructors.}
    \resumeItem{Built the production frontend in \textbf{React} and \textbf{TypeScript} and \textbf{Node.js} backend services integrating \textbf{Groq} and \textbf{Gemini} APIs for live tutoring workflows, supporting 60+ concurrent users with sub-2s response latency.}
    \resumeItem{Designed \textbf{PostgreSQL} schemas for authentication, progress tracking, and role-based learning analytics across student, instructor, and researcher personas.}
    \resumeItem{Implemented shared TypeScript contracts and validation across frontend and backend services, reducing integration defects by 30\% and accelerating feature delivery across sprint cycles.}
    \resumeItem{Shipped 8+ major module updates on 2-week iteration cycles without disrupting live classroom usage.}
  \resumeItemListEnd"""

JAVA_COGNIZANT = r"""  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed customer-facing \textbf{Java/Spring Boot} REST APIs for registration, validation, and authentication workflows supporting \textbf{20K+ hourly peak transactions} across customer onboarding and account management.}
    \resumeItem{Implemented business rules and input-validation services in \textbf{Core Java} using \textbf{OOP} abstractions, \textbf{Collections}, and \textbf{exception handling}, reducing downstream processing errors by 18\% across high-volume registration flows.}
    \resumeItem{Authored parameterized \textbf{SQL} queries and stored-procedure integrations against \textbf{SQL Server} and \textbf{MongoDB} for customer profile and transactional data, supporting reliable reads/writes under peak onboarding traffic.}
    \resumeItem{Leveraged \textbf{Redis} for session and token caching on authentication endpoints, improving p95 response times by 30\% and lowering database load on hot read paths.}
    \resumeItem{Standardized REST request/response DTOs and error-handling contracts across microservices, cutting frontend-backend integration defects by 25\% and improving release stability for consuming web clients.}
    \resumeItem{Built automated test coverage with \textbf{JUnit} and \textbf{Cucumber} BDD scenarios on critical auth paths, reaching 70\% backend coverage; debugged production registration failures in \textbf{Agile} sprints using \textbf{Git}-based feature branches.}
  \resumeItemListEnd"""

SWE_COGNIZANT = r"""  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed customer-facing \textbf{Java/Spring Boot} REST APIs for registration, validation, and authentication workflows supporting \textbf{20K+ hourly peak transactions} across customer onboarding and account management.}
    \resumeItem{Implemented business rules and input-validation services in \textbf{Java} and \textbf{SQL}, reducing downstream processing errors by 18\% across high-volume registration flows.}
    \resumeItem{Leveraged \textbf{Redis} for session and token caching on authentication endpoints, improving p95 response times by 30\% and lowering database load on hot read paths.}
    \resumeItem{Standardized REST request/response contracts across microservices, cutting frontend-backend integration defects by 25\% and improving release stability for consuming teams.}
    \resumeItem{Built automated test coverage with \textbf{JUnit} and \textbf{Cucumber}, reaching 70\% backend coverage and reducing production regressions on critical auth paths.}
  \resumeItemListEnd"""

NODE_COGNIZANT = r"""  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed customer-facing features across \textbf{React} frontends and \textbf{Java/Spring Boot} REST APIs for registration, validation, and authentication workflows supporting \textbf{20K+ hourly peak transactions} across customer onboarding and account management.}
    \resumeItem{Implemented business rules and input-validation services in \textbf{Java} and \textbf{SQL}, reducing downstream processing errors by 18\% across high-volume registration flows.}
    \resumeItem{Leveraged \textbf{Redis} for session and token caching on authentication endpoints, improving p95 response times by 30\% and lowering database load on hot read paths.}
    \resumeItem{Standardized REST request/response contracts across microservices and React clients, cutting frontend-backend integration defects by 25\% and improving release stability for consuming teams.}
    \resumeItem{Built automated test coverage with \textbf{JUnit} and \textbf{Cucumber}, reaching 70\% backend coverage and reducing production regressions on critical auth paths.}
  \resumeItemListEnd"""

AI_COGNIZANT = r"""  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed customer-facing \textbf{Java/Spring Boot} REST APIs for registration, validation, and authentication workflows supporting \textbf{20K+ hourly peak transactions} across customer onboarding and account management.}
    \resumeItem{Leveraged \textbf{Redis} for session and token caching on authentication endpoints, improving p95 response times by 30\% and lowering database load on hot read paths.}
    \resumeItem{Built automated test coverage with \textbf{JUnit} and \textbf{Cucumber}, reaching 70\% backend coverage and reducing production regressions on critical auth paths.}
  \resumeItemListEnd"""

PYTHON_COGNIZANT = NODE_COGNIZANT

# --- Skills blocks ---

JAVA_SKILLS = r"""  \small{\item{
    \textbf{Languages:} Java, SQL, JavaScript, Python \\[1pt]
    \textbf{Backend:} Spring Boot, REST APIs, Microservices, OOP, Exception Handling, Collections \\[1pt]
    \textbf{Data \& Caching:} PostgreSQL, MongoDB, SQL Server, Redis \\[1pt]
    \textbf{Tools:} Git, Docker, Jenkins, GitHub Actions, Linux, Agile \\[1pt]
    \textbf{Testing:} JUnit, Cucumber \\[1pt]
    \textbf{Web:} HTML, CSS, JavaScript
  }}"""

NODE_SKILLS = r"""  \small{\item{
    \textbf{Languages:} TypeScript, JavaScript, SQL, Python, Java \\[1pt]
    \textbf{Frontend \& Backend:} React, Next.js, Node.js, Express.js, REST APIs, Microservices \\[1pt]
    \textbf{Data \& Cloud:} PostgreSQL, MongoDB, Redis, SQL Server, AWS, Docker, GitHub Actions, Linux \\[1pt]
    \textbf{Architecture:} REST APIs, Microservices, Authentication, RBAC, System Design
  }}"""

PYTHON_SKILLS = r"""  \small{\item{
    \textbf{Languages:} Python, TypeScript, SQL, JavaScript, Java \\[1pt]
    \textbf{Frontend \& Backend:} React, Flask, FastAPI, REST APIs, Microservices \\[1pt]
    \textbf{Data \& Cloud:} PostgreSQL, Supabase, MongoDB, Redis, AWS, Docker, GitHub Actions, Linux \\[1pt]
    \textbf{Architecture:} REST APIs, Microservices, Authentication, RBAC, System Design
  }}"""

AI_SKILLS = r"""  \small{\item{
    \textbf{Languages:} Python, TypeScript, SQL, Java \\[1pt]
    \textbf{LLM APIs:} OpenAI, Anthropic, Groq, Gemini \\[1pt]
    \textbf{AI \& ML:} LangChain, LlamaIndex, LangGraph, RAG, Prompt Engineering, Model Evaluation, Vector Search \\[1pt]
    \textbf{Backend \& Platform:} FastAPI, Node.js, React, REST APIs, PostgreSQL, Redis, Docker, Kubernetes \\[1pt]
    \textbf{Observability \& MLOps:} vLLM, Prometheus, Grafana, Terraform, GitHub Actions, AWS, GPU Inference \\[1pt]
    \textbf{Developer Tools:} Git, GitHub, Cursor, GitHub Copilot \\[1pt]
    \textbf{Testing:} Jest, JUnit
  }}"""


def _replace_experience_block(tex: str, usf: str, cognizant: str) -> str:
    pattern = (
        r"  \\resumeSubheading\s*\n"
        r"    \{University of South Florida\}.*?"
        r"  \\resumeItemListEnd\s*\n\n"
        r"  \\resumeSubheading\s*\n"
        r"    \{Cognizant Technology Solutions\}.*?"
        r"  \\resumeItemListEnd"
    )
    match = re.search(pattern, tex, flags=re.DOTALL)
    if not match:
        raise ValueError("Could not locate experience block in resume template")
    return tex[: match.start()] + usf + "\n\n" + cognizant + tex[match.end() :]


def _replace_skills_block(tex: str, skills: str) -> str:
    start = tex.index(r"  \small{\item{")
    end = tex.index("  }}", start) + 4
    return tex[:start] + skills + tex[end:]


def _project_by_id(project_id: int) -> dict:
    return next(p for p in PROJECTS if p["id"] == project_id)


def _build(
    *,
    filename: str,
    projects: list[dict],
    identity: str,
    usf: str,
    cognizant: str,
    skills: str,
    max_projects: int = 2,
    max_bullets: int | None = None,
) -> None:
    tex = replace_projects_section(
        BASE, projects[:max_projects], BASE, identity
    )
    tex = _replace_experience_block(tex, usf, cognizant)
    tex = _replace_skills_block(tex, skills)
    out_path = OUT / filename
    out_path.write_text(tex, encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> None:
    # Project 9 mirrors Cognizant (registration/auth APIs, same metrics) — use only
    # Project 10 so projects add skills not already covered by experience.
    java_projects = [
        materialize_project_for_identity(_project_by_id(10), "backend_engineer"),
    ]

    node_projects = [
        materialize_project_for_identity(_project_by_id(7), "fullstack_engineer"),
        materialize_project_for_identity(_project_by_id(8), "fullstack_engineer"),
    ]

    ai_projects = [
        materialize_project_for_identity(_project_by_id(i), "ai_platform_engineer")
        for i in (4, 3, 2, 1)
    ]

    python_projects = [
        materialize_project_for_identity(_project_by_id(8), "fullstack_engineer"),
        materialize_project_for_identity(_project_by_id(7), "fullstack_engineer"),
    ]

    _build(
        filename="Tarun_Mannava_Software_Engineer_Java.tex",
        projects=java_projects,
        identity="backend_engineer",
        usf=JAVA_USF,
        cognizant=JAVA_COGNIZANT,
        skills=JAVA_SKILLS,
        max_projects=1,
        max_bullets=4,
    )
    _build(
        filename="Tarun_Mannava_Software_Engineer_Node_TypeScript.tex",
        projects=node_projects,
        identity="fullstack_engineer",
        usf=NODE_USF,
        cognizant=NODE_COGNIZANT,
        skills=NODE_SKILLS,
    )
    _build(
        filename="Tarun_Mannava_Software_Engineer_Python_TypeScript.tex",
        projects=python_projects,
        identity="fullstack_engineer",
        usf=PYTHON_USF,
        cognizant=PYTHON_COGNIZANT,
        skills=PYTHON_SKILLS,
    )
    _build(
        filename="Tarun_Mannava_AI_Engineer.tex",
        projects=ai_projects,
        identity="ai_platform_engineer",
        usf=AI_USF,
        cognizant=AI_COGNIZANT,
        skills=AI_SKILLS,
        max_projects=4,
        max_bullets=3,
    )


if __name__ == "__main__":
    main()
