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
