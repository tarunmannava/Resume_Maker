from backend.app.services.latex_projects import (
    force_replace_projects_section,
    projects_contain_ai_jargon,
    replace_projects_section,
)
from backend.app.services.latex_skills import sanitize_skills_section
from backend.app.services.project_framing import extract_resume_supported_terms, select_projects
from backend.app.services.rewrite_strategy import classify_target_role_identity
from backend.app.models.schemas import RewriteRequest
from backend.app.services import rewrite as rewrite_service

JAVA_JD = """
Junior Software Developer (Java). Core Java, OOP, Collections, Exception Handling.
Spring Boot. RESTful APIs. MySQL PostgreSQL Oracle. HTML CSS JavaScript. Git. debugging Agile.
"""

BAD_LLM_OUTPUT = r"""
\section{PROJECTS}
\resumeSubHeadingListStart

  \vspace{-2pt}\item[]
  \begin{tabular*}{0.97\textwidth}[t]{l}
    \textbf{Centralized Prompt Registry for AI-Powered Educational Content} \\
    \small\textit{Python, FastAPI, React, PostgreSQL, OpenAI, Docker}
  \end{tabular*}\vspace{-7pt}
  \resumeItemListStart
    \resumeItem{LangGraph multi-agent orchestration.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
"""


def test_java_jd_wins_over_ai_engineer_ui_selection():
    identity = classify_target_role_identity(JAVA_JD, "clinical llm langchain resume", "AI Engineer")
    assert identity == "backend_engineer"


def test_junior_software_developer_java_phrase():
    jd = "Junior Software Developer (Java). HTML CSS JavaScript. Git. Agile."
    identity = classify_target_role_identity(jd, "llm langchain", "Software Engineer")
    assert identity == "backend_engineer"
    projects = select_projects("Software Engineer", jd, identity)
    assert projects[0]["id"] == 3


def test_inject_replaces_resumeProject_two_arg_format():
    projects = select_projects("Software Engineer", JAVA_JD, "backend_engineer")
    original = r"""
\newcommand{\resumeProject}[2]{
  \textbf{#1} \\
  \small\textit{#2}
}
\newcommand{\resumeProjectHeading}[1]{}
"""
    llm = r"""
\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{Centralized Prompt Registry for AI}{Python, LangGraph, FastAPI}
  \resumeItemListStart
    \resumeItem{LangGraph multi-agent.}
  \resumeItemListEnd

  \resumeProject{Autonomous Multi-Agent Platform}{Python, LangGraph}
  \resumeItemListStart
    \resumeItem{token tracing.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
"""
    fixed = force_replace_projects_section(llm, projects, original, "backend_engineer")
    assert "Prompt Registry" not in fixed
    assert "LangGraph" not in fixed
    assert "Configuration Management" in fixed or "High-Throughput" in fixed or "Distributed Workflow" in fixed
    assert "\\resumeProject{" in fixed


def test_sanitize_removes_oracle_and_langgraph():
    skills = r"""
\section{TECHNICAL SKILLS}
\begin{itemize}
  \small{\item{
    \textbf{Languages:} Java \;|\; SQL (Oracle, PostgreSQL) \\[1pt]
    \textbf{AI:} LangChain \;|\; LangGraph \;|\; Prompt Engineering
  }}
\end{itemize}
\section{EXPERIENCE}
"""
    supported = extract_resume_supported_terms("Java Spring Boot PostgreSQL Redis LangChain")
    cleaned = sanitize_skills_section(
        skills, supported, [], "backend_engineer", "Java PostgreSQL LangChain"
    )
    assert "Oracle" not in cleaned
    assert "LangGraph" not in cleaned


def test_sanitize_normalizes_malformed_skill_pipes():
    skills = r"""
\section{TECHNICAL SKILLS}
\begin{itemize}
  \small{\item{
    \textbf{Testing \& Methodologies:} Jest \;|\; Cypress \;|\| Cucumber \;|\| Agile \\[1pt]
    \textbf{Programming Concepts:} OOP \;|\; Collections \;|\| Exception Handling \;|\| Git
  }}
\end{itemize}
\section{EXPERIENCE}
"""
    cleaned = sanitize_skills_section(
        skills, set(), [], "backend_engineer", skills
    )

    assert r"\;|\|" not in cleaned
    assert r"Jest \;|\; Cypress \;|\; Cucumber \;|\; Agile" in cleaned
    assert r"Collections \;|\; Exception Handling \;|\; Git" in cleaned


def test_sanitize_preserves_dollar_pipe_style_from_original_skills():
    skills = r"""
\section{TECHNICAL SKILLS}
\begin{itemize}
  \small{\item{
    \textbf{Languages:} Java \;|\; Python \;|\| SQL \\[1pt]
    \textbf{AI:} LangGraph \;|\; Prompt Engineering
  }}
\end{itemize}
\section{EXPERIENCE}
"""
    original = r"""
\section{SKILLS}
\begin{itemize}
  \small{\item{
    \textbf{Languages:} Java $|$ Python $|$ SQL \\[1pt]
  }}
\end{itemize}
\section{EXPERIENCE}
"""
    cleaned = sanitize_skills_section(
        skills, {"java", "python", "sql"}, [], "backend_engineer", original
    )

    assert r"\;|\;" not in cleaned
    assert r"\;|\|" not in cleaned
    assert "Java $|$ Python $|$ SQL" in cleaned
    assert "LangGraph" not in cleaned


def test_rewrite_preserves_java_experience_and_projects(monkeypatch):
    original = r"""
\documentclass{article}
\newcommand{\resumeItem}[1]{\item #1}
\newcommand{\resumeSubheading}[4]{\item #1 #2 #3 #4}
\newcommand{\resumeProjectHeading}[1]{\item #1}
\newcommand{\resumeProject}[2]{\resumeProjectHeading{#1}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\begin{document}
\section{EXPERIENCE}
\resumeSubHeadingListStart
\resumeSubheading{Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
\resumeItemListStart
\resumeItem{Developed Java/Spring Boot REST APIs with SQL, Redis, JUnit, and Cucumber.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{PROJECTS}
\resumeSubHeadingListStart
\resumeProjectHeading{AutoDocs PR Documentation System}
\resumeItemListStart
\resumeItem{Built documentation workflows with FastAPI and RabbitMQ.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{SKILLS}
\begin{itemize}\item Java Spring Boot SQL Redis JUnit Cucumber React TypeScript\end{itemize}
\end{document}
"""
    model_output = r"""
\documentclass{article}
\begin{document}
\section{TECHNICAL SKILLS}
\begin{itemize}\item Java Spring Boot SQL Oracle\end{itemize}
\section{EXPERIENCE}
\resumeSubHeadingListStart
\resumeSubheading{Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
\resumeItemListStart
\resumeItem{Developed Java/Spring Boot REST APIs.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{PROJECTS}
\resumeSubHeadingListStart
\resumeProjectHeading{AutoDocs PR Documentation System}
\resumeItemListStart
\resumeItem{Developed documentation workflows with asynchronous message queues.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{EDUCATION}
\end{document}
"""

    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (model_output, "test"),
    )

    response = rewrite_service.rewrite_resume(
        RewriteRequest(
            job_description=JAVA_JD,
            resume_latex=original,
            rewrite_mode="transferable",
        )
    )

    assert "Cognizant" in response.rewritten_latex
    assert "AutoDocs" in response.rewritten_latex

