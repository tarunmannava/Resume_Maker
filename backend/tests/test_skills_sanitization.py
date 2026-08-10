from backend.app.services.latex_skills import sanitize_skills_section
from backend.app.services.project_framing import extract_resume_supported_terms
from backend.app.services.rewrite_strategy import classify_target_role_identity

JAVA_JD = """
Junior Software Developer (Java). Core Java, OOP, Collections, Exception Handling.
Spring Boot. RESTful APIs. MySQL PostgreSQL Oracle. HTML CSS JavaScript. Git. debugging Agile.
"""


def test_java_jd_wins_over_ai_engineer_ui_selection():
    identity = classify_target_role_identity(JAVA_JD, "clinical llm langchain resume", "AI Engineer")
    assert identity == "backend_engineer"


def test_junior_software_developer_java_phrase():
    jd = "Junior Software Developer (Java). HTML CSS JavaScript. Git. Agile."
    identity = classify_target_role_identity(jd, "llm langchain", "Software Engineer")
    assert identity == "backend_engineer"


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
