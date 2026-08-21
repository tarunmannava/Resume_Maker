import pytest
from backend.app.models.schemas import RewriteRequest
from backend.app.services.rewrite import rewrite_resume
from backend.app.services.job_analyzer import detect_target_stack

# Load sample resume LaTeX matching main (1).tex
SAMPLE_RESUME_LATEX = r"""
\documentclass[a4paper,10pt]{article}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\geometry{a4paper, top=0.35in, bottom=0.35in, left=0.4in, right=0.4in}

\newcommand{\resumeItem}[1]{\item\small{#1}}
\newcommand{\resumeSubheading}[4]{
  \vspace{0pt}\item
  \textbf{#1} \\
  \textit{\small #2} \\
  \small #3 -- #4
  \vspace{2pt}
}
\newcommand{\resumeProject}[2]{
  \vspace{0pt}\item[]
  \textbf{#1} \\
  \small\textit{#2}
  \vspace{2pt}
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.15in, label={$\bullet$}]}
\newcommand{\resumeItemListEnd}{\end{itemize}}

\begin{document}

\begin{center}
  {\Huge \textbf{Tarun Mannava}} \\[4pt]
  \small Tampa, FL $|$ +1 (656) 203-7074 \\[4pt]
  \textit{Software Engineer with 2+ years of experience building scalable Java and Spring Boot backend systems.}
\end{center}

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}]
  \small{\item{
    \textbf{Backend:} Java, Spring Boot, Microservices \\[1pt]
    \textbf{Databases:} PostgreSQL, Redis
  }}
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida}{Graduate Researcher, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Delivered a web platform using React, TypeScript, and Python Flask.}
  \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed Java 11 / Spring Boot microservices for REST APIs.}
  \resumeItemListEnd
\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProject{Java Issue Tracking and Team Workflow Management Application}{Java, Spring Boot, PostgreSQL}
  \resumeItemListStart
    \resumeItem{Built a Java Spring Boot backend exposing REST APIs with PostgreSQL.}
  \resumeItemListEnd
\resumeSubHeadingListEnd

\end{document}
"""

JAVA_JD = """
Required: Java 17, Spring Boot, Spring Security, Microservices, PostgreSQL, Redis, Docker, JUnit 5.
We are looking for a Senior Java Developer to build high-concurrency backend services and distributed caching.
"""

AI_JD = """
Required: Python, LLMs, LangChain, RAG, Vector Search, OpenAI API, FastAPI, PostgreSQL, Docker.
We need an AI Engineer to build RAG retrieval pipelines and AI agent workflows.
"""

PYTHON_JD = """
Required: Python, FastAPI, Flask, AsyncIO, PostgreSQL, Redis, Docker, pytest.
Looking for a Python Backend Engineer to build scalable microservices and data pipelines.
"""

NODE_JD = """
Required: TypeScript, Node.js, Express.js, React, REST APIs, PostgreSQL, Jest, Docker.
Seeking a Full Stack Node.js Engineer to build end-to-end web applications and Node APIs.
"""


def test_detect_target_stack_matrix():
    assert detect_target_stack(JAVA_JD) == "java"
    assert detect_target_stack(AI_JD) in ("ai", "python")
    assert detect_target_stack(PYTHON_JD) == "python"
    assert detect_target_stack(NODE_JD) == "node"


def test_java_jd_pipeline_preserves_java_project_and_reorders_cognizant(monkeypatch):
    from backend.app.services import rewrite as rewrite_service

    mock_llm_output = r"""
\documentclass[a4paper,10pt]{article}
\begin{document}
\begin{center}
  {\Huge \textbf{Tarun Mannava}} \\[4pt]
  \textit{Software Engineer with 2+ years of experience building Java and Spring Boot microservices.}
\end{center}

\section{SKILLS}
\begin{itemize}
  \item \textbf{Backend:} Java, Spring Boot, REST APIs
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida}{Graduate Researcher}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Python Flask APIs}
  \resumeItemListEnd
  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Java Spring Boot REST APIs}
  \resumeItemListEnd
\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProject{Java Issue Tracking Application}{Java, Spring Boot, PostgreSQL}
  \resumeItemListStart
    \resumeItem{Built Java Spring Boot backend.}
  \resumeItemListEnd
\resumeSubHeadingListEnd
\end{document}
"""
    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (mock_llm_output, "test", None),
    )

    req = RewriteRequest(
        resume_latex=SAMPLE_RESUME_LATEX,
        job_description=JAVA_JD,
        selected_stack_override="java",
    )
    res = rewrite_service.rewrite_resume(req)
    output = res.rewritten_latex

    # Cognizant MUST be before USF
    cog_pos = output.find("Cognizant Technology Solutions")
    usf_pos = output.find("University of South Florida")
    assert cog_pos != -1
    assert usf_pos != -1
    assert cog_pos < usf_pos

    # Java project preserved (not replaced with QA Assistant)
    assert "Java" in output
    assert "QA Assistant" not in output


def test_node_jd_pipeline_swaps_projects_and_adapts_tech_stack(monkeypatch):
    from backend.app.services import rewrite as rewrite_service

    mock_llm_output = r"""
\documentclass[a4paper,10pt]{article}
\begin{document}
\begin{center}
  {\Huge \textbf{Tarun Mannava}} \\[4pt]
  \textit{Full Stack Engineer with 2+ years of experience building Node.js applications.}
\end{center}

\section{SKILLS}
\begin{itemize}
  \item \textbf{Core:} TypeScript, Node.js
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida}{Graduate Researcher}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{React and Node.js APIs}
  \resumeItemListEnd
\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProject{Old Project}{Java}
  \resumeItemListStart
    \resumeItem{Old bullet}
  \resumeItemListEnd
\resumeSubHeadingListEnd
\end{document}
"""
    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (mock_llm_output, "test", None),
    )

    req = RewriteRequest(
        resume_latex=SAMPLE_RESUME_LATEX,
        job_description=NODE_JD,
        selected_stack_override="node",
    )
    res = rewrite_service.rewrite_resume(req)
    output = res.rewritten_latex

    # Java project replaced with catalog projects (QA Assistant / PR Doc Agent)
    assert "Java Issue Tracking" not in output
    # Node stack adapted
    assert "TypeScript" in output or "Node.js" in output
