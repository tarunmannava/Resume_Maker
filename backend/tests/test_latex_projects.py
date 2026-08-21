from pathlib import Path

from backend.app.services.latex_projects import force_replace_projects_section, replace_projects_section
from backend.app.services.project_framing import select_projects

JAVA_JD = """
Junior Software Developer (Java). Core Java, OOP, Collections, Exception Handling.
Spring Boot. RESTful APIs. MySQL PostgreSQL. HTML CSS JavaScript. Git. debugging Agile.
"""


def test_java_jd_always_includes_project_3():
    projects = select_projects("Software Engineer", JAVA_JD, "backend_engineer")
    ids = [p["id"] for p in projects]
    assert 3 in ids


def test_replace_projects_section_in_resume_template():
    resume = Path(__file__).resolve().parents[2] / "resume.tex"
    original = resume.read_text(encoding="utf-8")
    projects = select_projects("Software Engineer", JAVA_JD, "backend_engineer")

    replaced = replace_projects_section(original, projects, original, "backend_engineer")

    assert projects[0]["title"] in replaced
    assert "Java" in replaced or "Spring Boot" in replaced


def test_replace_projects_section_inserts_when_missing():
    original = r"""
\documentclass{article}
\newcommand{\resumeProject}[2]{\textbf{#1} #2}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\newcommand{\resumeItem}[1]{\item #1}
\begin{document}
\section{EXPERIENCE}
\resumeSubHeadingListStart
\resumeSubHeadingListEnd
\section{EDUCATION}
\end{document}
"""
    projects = select_projects("Software Engineer", JAVA_JD, "backend_engineer")

    replaced = replace_projects_section(original, projects, original, "backend_engineer")

    assert "\\section{PROJECTS}" in replaced
    assert replaced.index("\\section{PROJECTS}") < replaced.index("\\section{EDUCATION}")
    assert projects[0]["title"] in replaced


def test_force_replace_removes_duplicate_ai_project_sections():
    original = r"""
\newcommand{\resumeProject}[2]{\resumeProjectHeading{#1}}
\newcommand{\resumeProjectHeading}[1]{}
"""
    duplicate_output = r"""
\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProjectHeading{Autonomous Multi-Agent Research Platform}
  \resumeItemListStart
    \resumeItem{Implemented LangGraph agents.}
  \resumeItemListEnd
\resumeSubHeadingListEnd
\section{EDUCATION}
\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProjectHeading{Centralized Prompt Registry for AI Experimentation}
  \resumeItemListStart
    \resumeItem{Built prompt registry workflows.}
  \resumeItemListEnd
\resumeSubHeadingListEnd
\section{CERTIFICATIONS}
"""
    projects = select_projects("Software Engineer", JAVA_JD, "backend_engineer")

    replaced = force_replace_projects_section(
        duplicate_output, projects, original, "backend_engineer"
    )

    assert replaced.count("\\section{PROJECTS}") == 1
    assert "Configuration Management" in replaced or "High-Throughput" in replaced or "Ledger" in replaced
    assert "Multi-Agent" not in replaced
    assert "Prompt Registry" not in replaced


def test_cap_projects_at_max_removes_third_project():
    from backend.app.services.latex_projects import cap_projects_at_max

    three_projects_latex = r"""
\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{Project Alpha}{React, TypeScript}
  \resumeItemListStart
    \resumeItem{Built frontend UI.}
  \resumeItemListEnd

  \resumeProject{Project Beta}{Java, Spring Boot}
  \resumeItemListStart
    \resumeItem{Built microservice.}
  \resumeItemListEnd

  \resumeProject{Project Gamma}{Python, FastAPI}
  \resumeItemListStart
    \resumeItem{Built API service.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
"""
    capped = cap_projects_at_max(three_projects_latex, max_projects=2)
    assert "Project Alpha" in capped
    assert "Project Beta" in capped
    assert "Project Gamma" not in capped
    assert r"\resumeSubHeadingListEnd" in capped


def test_custom_resume_project_preserved(monkeypatch):
    from backend.app.models.schemas import RewriteRequest
    from backend.app.services import rewrite as rewrite_service

    custom_resume = r"""
\documentclass{article}
\begin{document}
\section{EXPERIENCE}
\begin{itemize}\item Cognizant Java Developer\end{itemize}
\section{PROJECTS}
\begin{itemize}
  \item Custom Java Payment Gateway Integration (Java, Spring Boot)
\end{itemize}
\section{SKILLS}
\begin{itemize}\item Java Spring Boot PostgreSQL\end{itemize}
\end{document}
"""
    llm_output = r"""
\documentclass{article}
\begin{document}
\section{EXPERIENCE}
\begin{itemize}\item Cognizant Java Developer\end{itemize}
\section{PROJECTS}
\begin{itemize}
  \item Custom Java Payment Gateway Integration (Java, Spring Boot)
\end{itemize}
\section{SKILLS}
\begin{itemize}\item Java Spring Boot PostgreSQL\end{itemize}
\end{document}
"""
    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (llm_output, "test"),
    )

    response = rewrite_service.rewrite_resume(
        RewriteRequest(
            job_description="Java Developer. Spring Boot PostgreSQL.",
            resume_latex=custom_resume,
            rewrite_mode="transferable",
        )
    )

    assert "Custom Java Payment Gateway Integration" in response.rewritten_latex


def test_irrelevant_project_replaced_with_catalog(monkeypatch):
    from backend.app.models.schemas import RewriteRequest
    from backend.app.services import rewrite as rewrite_service

    irrelevant_resume = r"""
\documentclass{article}
\begin{document}
\section{EXPERIENCE}
\begin{itemize}\item Cognizant Java Developer\end{itemize}
\section{PROJECTS}
\begin{itemize}
  \item Autonomous Multi-Agent Prompt Registry with LangGraph
\end{itemize}
\section{SKILLS}
\begin{itemize}\item Java Spring Boot PostgreSQL\end{itemize}
\end{document}
"""
    llm_output = irrelevant_resume

    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (llm_output, "test"),
    )

    response = rewrite_service.rewrite_resume(
        RewriteRequest(
            job_description="Java Developer. Spring Boot PostgreSQL.",
            resume_latex=irrelevant_resume,
            rewrite_mode="transferable",
        )
    )

    assert "Prompt Registry" not in response.rewritten_latex
    assert "LangGraph" not in response.rewritten_latex
    assert "Configuration Management" in response.rewritten_latex or "High-Throughput" in response.rewritten_latex or "Distributed Workflow" in response.rewritten_latex
