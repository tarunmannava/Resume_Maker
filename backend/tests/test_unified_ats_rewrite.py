import re
import pytest
from unittest.mock import MagicMock, patch

from backend.app.models.schemas import RewriteRequest, RewriteResponse
from backend.app.services import rewrite as rewrite_service
from backend.app.services.job_analyzer import detect_target_stack
from backend.app.services.latex import latex_to_text, sanitize_latex_escaping
from backend.app.services.scoring import score_keywords
from backend.app.services.keyword_extractor import extract_keywords


SAMPLE_BASE_RESUME = r"""\documentclass[letterpaper,11pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}

\newcommand{\resumeItem}[1]{\item\small{#1 \vspace{-2pt}}}
\newcommand{\resumeSubheading}[4]{\vspace{-2pt}\item\begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}\textbf{#1} & #2 \\ \textit{\small#3} & \textit{\small #4} \\ \end{tabular*}\vspace{-7pt}}
\newcommand{\resumeProject}[2]{\vspace{-2pt}\item\begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}\textbf{#1} & \textit{\small #2} \\ \end{tabular*}\vspace{-7pt}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeSep}{\textbar}
\newcommand{\resumeHeadingContact}{Seattle, WA \hspace{0.4em}\resumeSep\hspace{0.4em} \href{mailto:test@example.com}{test@example.com}}

\begin{document}
\begin{center}
    {\Huge \textbf{Tarun Mannava}} \\ \vspace{2pt}
    \resumeHeadingContact
\end{center}

\section{SUMMARY}
Backend Software Engineer with experience in distributed systems, REST APIs, and microservices.

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    \textbf{Languages:} Java, Python, TypeScript, SQL \\[1pt]
    \textbf{Backend:} Spring Boot, FastAPI, REST APIs, Microservices \\[1pt]
    \textbf{Databases \& Tools:} PostgreSQL, Redis, Docker, Git
  }}
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida}{Tampa, FL}
    {Graduate Researcher}{Aug 2023 -- May 2025}
    \resumeItemListStart
      \resumeItem{Developed asynchronous FastAPI services for autonomous multi-agent systems.}
      \resumeItem{Engineered distributed task pipelines reducing end-to-end latency by 35 percent.}
    \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Hyderabad, India}
    {Software Engineer}{Aug 2021 -- Jun 2023}
    \resumeItemListStart
      \resumeItem{Engineered Spring Boot microservices handling high-throughput policy validation.}
      \resumeItem{Optimized PostgreSQL database queries and integrated Redis caching to cut latency by 30 percent.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProject
    {AutoDocs -- Automated Documentation Generator}{Python, FastAPI, LLMs}
    \resumeItemListStart
      \resumeItem{Built an asynchronous pipeline analyzing Git commits and generating PR documentation.}
    \resumeItemListEnd
  \resumeProject
    {SkillBeacon -- Developer Analytics Engine}{Python, React, Redis}
    \resumeItemListStart
      \resumeItem{Created analytics dashboard processing developer skills benchmarks.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

\end{document}"""


# ---------------------------------------------------------------------------
# Test 1: Stack Detection & Manual Overrides Across All 5 Stacks
# ---------------------------------------------------------------------------

def test_stack_detection_all_5_scenarios():
    jd_dotnet = "Looking for a C# .NET Core engineer with ASP.NET Core, Entity Framework Core, and SQL Server."
    jd_java = "Senior Java Developer with Spring Boot, Microservices, Hibernate, and PostgreSQL."
    jd_node = "Fullstack Engineer with Node.js, TypeScript, React, Express, and GraphQL."
    jd_ai = "AI Engineer to build GenAI pipelines with LLMs, LangChain, LangGraph, RAG, and vector search."
    jd_python = "Backend Engineer with Python, FastAPI, AsyncIO, and PostgreSQL."

    assert detect_target_stack(jd_dotnet) == "dotnet"
    assert detect_target_stack(jd_java) == "java"
    assert detect_target_stack(jd_node) == "node"
    assert detect_target_stack(jd_ai) == "ai"
    assert detect_target_stack(jd_python) == "python"

    # Test user overrides
    assert detect_target_stack(jd_java, user_override="dotnet") == "dotnet"
    assert detect_target_stack(jd_java, user_override="C#") == "dotnet"
    assert detect_target_stack(jd_python, user_override="node") == "node"
    assert detect_target_stack(jd_dotnet, user_override="ai") == "ai"


# ---------------------------------------------------------------------------
# Test 2: Prompt Construction Injects ATS Criteria & Exact Gaps
# ---------------------------------------------------------------------------

def test_prompt_construction_injects_ats_gap_list_and_guardrails():
    req = RewriteRequest(
        job_description="Senior Java Developer with Spring Boot, Kafka, Docker, Kubernetes, and Redis.",
        resume_latex=SAMPLE_BASE_RESUME,
        target_location="San Francisco, CA",
        role_name="Senior Java Engineer",
    )

    missing = ["Kafka", "Kubernetes"]
    unsupported = []
    target_stack = "java"
    industry = "FinTech"

    prompt = rewrite_service.build_user_prompt(
        request=req,
        missing_terms=missing,
        unsupported_terms=unsupported,
        target_stack=target_stack,
        industry=industry,
    )

    assert "IDENTIFIED ATS CRITERIA & KEYWORD GAPS TO RESOLVE: Kafka, Kubernetes" in prompt
    assert "CONTEXTUAL ATS CRITERIA AUDIT & GAP RESOLUTION" in prompt
    assert "COGNIZANT EXPERIENCE (JAVA TARGET STACK)" in prompt
    assert "USF & PROJECTS RULE (JAVA): USF Graduate Researcher and Projects MUST STAY Python" in prompt
    assert "San Francisco, CA" in prompt


# ---------------------------------------------------------------------------
# Test 3: Ground Truth Stack Guardrails in System Prompt
# ---------------------------------------------------------------------------

def test_system_prompt_ats_screener_and_ground_truths():
    system_prompt = rewrite_service.build_system_prompt(align_titles=False)

    assert "CONTEXTUAL ATS SCREENER REASONING" in system_prompt
    assert "INTERNAL ATS AUDIT & GAP RECONCILIATION" in system_prompt
    assert "Tier 1 Knockout Requirements" in system_prompt
    assert "Tier 2 Contextual Evidence" in system_prompt
    assert "STRICTLY NO BOLDING OR HIGHLIGHTING KEYWORDS IN BULLETS" in system_prompt
    assert "COGNIZANT ROLE & DEFENSIBILITY GUARDRAIL" in system_prompt
    assert "USF & PROJECTS STACK & ARCHITECTURE MATRIX" in system_prompt


# ---------------------------------------------------------------------------
# Test 4: In-Place Bullet Adaptation & Zero Inline Bolding Verification
# ---------------------------------------------------------------------------

def test_remove_inline_bolding_from_bullets():
    dirty_latex = r"""
    \section{SKILLS}
    \textbf{Languages:} Java, Python, SQL
    \section{EXPERIENCE}
    \resumeSubHeadingListStart
      \resumeSubheading{Cognizant}{India}{Software Engineer}{2021-2023}
      \resumeItemListStart
        \resumeItem{Engineered \textbf{Spring Boot} microservices with \textbf{Redis} caching, cutting latency by \textbf{30\%}.}
        \resumeItem{Optimized \textbf{PostgreSQL} queries eliminating N+1 bottlenecks.}
      \resumeItemListEnd
    \resumeSubHeadingListEnd
    """
    clean_latex = rewrite_service.remove_inline_bolding_from_bullets(dirty_latex)

    assert r"\textbf{Spring Boot}" not in clean_latex
    assert r"\textbf{Redis}" not in clean_latex
    assert r"\textbf{PostgreSQL}" not in clean_latex
    assert r"\textbf{Languages:}" in clean_latex  # Category label remains bold!
    assert "Engineered Spring Boot microservices with Redis caching" in clean_latex


# ---------------------------------------------------------------------------
# Test 5: Target Location Contact Header Update
# ---------------------------------------------------------------------------

def test_update_contact_location():
    initial_latex = r"\newcommand{\resumeHeadingContact}{Seattle, WA \hspace{0.4em}\resumeSep\hspace{0.4em} \href{mailto:test@example.com}{test@example.com}}"
    updated = rewrite_service.update_contact_location(initial_latex, "New York, NY")
    assert "New York, NY" in updated
    assert "Seattle, WA" not in updated


# ---------------------------------------------------------------------------
# Test 6: LaTeX Truncation & List Repair Engine
# ---------------------------------------------------------------------------

def test_repair_truncated_latex():
    incomplete_latex = r"""\begin{document}
    \section{EXPERIENCE}
    \resumeSubHeadingListStart
      \resumeSubheading{Cognizant}{India}{Software Engineer}{2021-2023}
      \resumeItemListStart
        \resumeItem{Engineered Spring Boot microservices.}
    """
    repaired = rewrite_service.repair_truncated_latex(incomplete_latex)
    assert r"\resumeItemListEnd" in repaired
    assert r"\resumeSubHeadingListEnd" in repaired
    assert r"\end{document}" in repaired


# ---------------------------------------------------------------------------
# Test 7: End-to-End Mocked Rewrite Pipeline Execution
# ---------------------------------------------------------------------------

@patch.object(rewrite_service, "generate_rewrite")
def test_end_to_end_rewrite_pipeline_mocked(mock_generate):
    mock_rewritten_latex = SAMPLE_BASE_RESUME.replace(
        "Engineered Spring Boot microservices handling high-throughput policy validation.",
        "Engineered Spring Boot microservices with Kafka streaming and Redis caching, processing 450 req/sec at sub-50ms p95 latency."
    )
    mock_generate.return_value = (mock_rewritten_latex, "gemini", None)

    req = RewriteRequest(
        job_description="Looking for Java Spring Boot developer with Kafka, Redis, and high-throughput microservices experience.",
        resume_latex=SAMPLE_BASE_RESUME,
        target_location="Austin, TX",
        target_match_threshold=80,
    )

    resp = rewrite_service.rewrite_resume(req)

    assert isinstance(resp, RewriteResponse)
    assert resp.target_met is True or resp.match_score > 0
    assert "Kafka" in resp.rewritten_latex
    assert "Austin, TX" in resp.rewritten_latex
    assert r"\textbf{" not in resp.rewritten_latex.split(r"\resumeItemListStart")[1].split(r"\resumeItemListEnd")[0]
    assert len(resp.changes_made) >= 2
