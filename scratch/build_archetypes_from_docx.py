# -*- coding: utf-8 -*-
"""
Generate the 5 canonical base LaTeX archetypes directly from the 5 ground-truth DOCX files.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.docx import convert_tex_to_docx

ARCHETYPES_DIR = ROOT / "backend" / "app" / "templates" / "archetypes"
ARCHETYPES_DIR.mkdir(parents=True, exist_ok=True)

LATEX_PREAMBLE = r"""\documentclass[a4paper,10pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
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
\usepackage{mathptmx}
\usepackage{geometry}
\usepackage{setspace}
\usepackage{anyfontsize}

\geometry{
  a4paper,
  top=0.35in,
  bottom=0.35in,
  left=0.4in,
  right=0.4in
}

\setstretch{1.0}
\renewcommand{\normalsize}{\fontsize{10}{12}\selectfont}
\renewcommand{\small}{\fontsize{10}{12}\selectfont}
\normalsize

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-10pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-7pt}]

\newcommand{\resumeSep}{\textbullet}

\newcommand{\resumeItem}[1]{
  \item\small{#1}
}

\newcommand{\resumeSubheading}[4]{%
  \vspace{0pt}\item
  \textbf{#1} \\
  \textit{\small #2} \\
  \small #3 -- #4
  \vspace{2pt}
}

\newcommand{\resumeProject}[2]{%
  \vspace{0pt}\item[]
  \textbf{#1} \\
  \small\textit{#2}
  \vspace{2pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}

\newcommand{\resumeItemListStart}{%
  \begin{itemize}[leftmargin=0.15in, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt, label={$\bullet$}]%
}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{2pt}}
"""

# ==============================================================================
# 1. AI STACK ARCHETYPE (TarunMannava.docx)
# ==============================================================================
AI_TEX = LATEX_PREAMBLE + r"""\newcommand{\resumeHeadingContact}{%
  Seattle, WA \hspace{0.4em}\resumeSep\hspace{0.4em}+1 (656) 203-7074 \hspace{0.4em}\resumeSep\hspace{0.4em}\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://github.com/tarunmannava}{GitHub}%
}

\begin{document}

\begin{center}
  {\Huge \textbf{TARUN MANNAVA}} \\[4pt]
  \small
  \resumeHeadingContact
\end{center}

\vspace{-10pt}

\section{SUMMARY}
AI \& Software Engineer with 4+ years of experience engineering scalable backend and production LLM systems. Specializing in LangGraph multi-agent orchestration, MCP tool integration, Agentic Corrective RAG, and LangSmith evaluation pipelines. Backed by an enterprise foundation in high-throughput microservices, asynchronous execution, PostgreSQL, Redis caching, and scalable cloud infrastructure on AWS.

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    \textbf{GenAI \& Agents:} LangChain, LangGraph, StateGraph, Supervisor-Worker, Tool Calling, Agentic RAG, Corrective RAG, Hybrid Search, Reranking, MCP, A2A, Prompt Engineering \\[1pt]
    \textbf{LLMOps:} LangSmith Tracing/Evals/Datasets, RAGAS, LLM-as-Judge, Golden Sets, Citation/Hallucination Evals, Cost/Latency Tracking \\[1pt]
    \textbf{Languages:} Python, SQL, TypeScript, JavaScript, Java \\[1pt]
    \textbf{Backend:} FastAPI, Django, Flask, AsyncIO, Java 11, Spring Boot, REST, WebSockets, Microservices, Pydantic, SQLAlchemy, Spring Data JPA/Hibernate \\[1pt]
    \textbf{Retrieval:} PostgreSQL (pgvector) / Supabase, Qdrant, Pinecone, SQL Server, MongoDB, HNSW Indexing, Embeddings, BM25+Dense + RRF, Reranking \\[1pt]
    \textbf{Cloud \& Infra:} AWS (EC2, S3, RDS, Lambda, Cognito, CloudWatch), GCP (Vertex AI, Cloud Run, Cloud Storage), Azure (Blob Storage, App Services), Docker, Kubernetes, Linux, GitHub Actions, Redis, RabbitMQ \\[1pt]
    \textbf{Auth/Test:} OAuth2 PKCE, JWT, AWS Cognito, Spring Security, pytest, JUnit 5, Mockito
  }}
\end{itemize}

\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{JobPilot: Conversational Job-Search \& Ranking Agent}{Python, LangGraph, LangChain, MCP, Dice MCP, LangSmith}
  \resumeItemListStart
    \resumeItem{Built a conversational agent that extracts a user's resume and job preferences through natural-language chat, confirming extracted criteria with the user before taking any downstream action.}
    \resumeItem{Integrated the Dice MCP server as a tool-use client to retrieve live job listings, consuming an MCP server end-to-end after building MCP servers in AutoDocs.}
    \resumeItem{Implemented a resume-to-listing ranking step that scores and orders retrieved jobs against the user's parsed resume and stated preferences.}
    \resumeItem{Instrumented the agent with LangSmith tracing and pass/fail scoring on tool-call correctness, giving visibility into the confirmation, retrieval, and ranking steps of each run.}
  \resumeItemListEnd

  \resumeProject{AutoDocs: Event-Driven MCP \& Multi-Agent Documentation System}{Python, FastAPI, MCP, A2A, LangGraph, LangChain, RabbitMQ, WebSockets, Supabase, GitHub Webhooks, LangSmith}
  \resumeItemListStart
    \resumeItem{Built an event-driven documentation system receiving GitHub pull-request webhooks through FastAPI, validating HMAC-SHA256 signatures and enforcing idempotent delivery persistence in Supabase.}
    \resumeItem{Implemented asynchronous job processing with RabbitMQ, separating webhook ingestion from repository analysis and long-running documentation workflows with retry and failure handling.}
    \resumeItem{Implemented WebSocket-based real-time job updates, streaming repository-analysis status and agent progress to connected clients while supporting connection recovery and graceful handling of dropped connections.}
    \resumeItem{Designed Model Context Protocol (MCP) code-intelligence servers using AST analysis to extract class and function call graphs and provide structural repository context to LLMs.}
    \resumeItem{Architected dynamic task-routing multi-agent workflows with LangGraph to analyze code changes and generate contextual documentation with deterministic verification guardrails.}
    \resumeItem{Instrumented full LLM observability with LangSmith, tracing MCP tool-call sequences and LangGraph routing decisions per run and scoring each against expected tool-call patterns, achieving a 90\%+ pass rate on tool-call correctness.}
  \resumeItemListEnd

  \resumeProject{FinScope: Hierarchical Earnings Intelligence Graph}{Python, LangGraph, LangChain, SEC-API, Tavily, LangSmith}
  \resumeItemListStart
    \resumeItem{Built a hierarchical multi-agent system for earnings analysis that routes filings through specialized analyst nodes, synthesizing ratio analysis and risk review into a structured investment memo.}
    \resumeItem{Implemented LangGraph supervisor-worker routing with shared Pydantic financial state, delegating fetch, calculation, and review steps across isolated nodes with conditional edges for low-confidence escalation.}
    \resumeItem{Integrated SEC-API and Tavily web search as LangChain tool nodes to retrieve live filings and market context, adding numeric validation to block incorrect margin and return calculations before synthesis.}
    \resumeItem{Implemented human-approval interrupt that pauses execution for analyst review when confidence scores fall below threshold, with checkpointed state for resume and audit.}
    \resumeItem{Architected deterministic verification guardrails requiring sourced numbers for every ratio claim, rejecting unsupported outputs and retrying failed tool calls with backoff.}
    \resumeItem{Instrumented full trajectory observability with LangSmith, tracing node-level decisions and tool-call sequences per run and scoring each against a 20-ticker golden dataset for numeric accuracy and faithfulness, with per-node latency and cost tracking.}
  \resumeItemListEnd

  \resumeProject{ProofStack: MCP-Backed Corrective Retrieval Graph}{Python, FastAPI, LangGraph, LangChain MCP, PostgreSQL (pgvector), Tavily, LangSmith}
  \resumeItemListStart
    \resumeItem{Built a corrective RAG system that answers questions over internal docs by routing all retrieval through MCP tool servers, falling back to web search only when graded evidence is insufficient.}
    \resumeItem{Implemented LangGraph retrieve-grade-rewrite loop that rewrites ambiguous queries, retrieves via MCP tools, grades document relevance, and regenerates answers until grounding threshold is met.}
    \resumeItem{Designed three Model Context Protocol servers as LangChain tools: vector\_search over PostgreSQL (pgvector HNSW) with dense-lexical hybrid ranking, docs\_sql for structured records, and web\_search via Tavily, with timeout, retry, and schema validation.}
    \resumeItem{Implemented WebSocket-compatible FastAPI serving layer streaming retrieval status and token output while enforcing citation-required generation with abstention on low-evidence queries.}
    \resumeItem{Architected verification guardrails with grounding-score gates and Pydantic-validated RAG state to prevent hallucinated citations and enforce idempotent query handling.}
    \resumeItem{Instrumented full LLM observability with LangSmith, tracing MCP tool-call sequences and routing decisions per run and scoring each against a 50-query golden set for faithfulness, recall@5, and citation precision, with per-route cost and p50/p95 tracking.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EXPERIENCE}
\resumeSubHeadingListStart

  \resumeSubheading
    {University of South Florida}{Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Designed and maintained a production AI \& Health Literacy web platform for the USF SHIELD Lab, building 13 interactive modules in React and TypeScript that serve 60+ biomedical students and faculty in daily coursework and research activities.}
    \resumeItem{Engineered a Python/FastAPI backend and a real-time dual-model sandbox integrating Groq and Hugging Face LLM APIs, with semantic grading rubrics, milestone detection, and caching that keeps interactive response latency below 2 seconds.}
    \resumeItem{Implemented an in-browser prompt evaluation engine using Transformers.js (WASM/ONNX) to compute cosine-similarity embedding scoring locally, providing zero-latency, privacy-preserving feedback on prompt structure and constraints.}
    \resumeItem{Built authentication and session management with Hugging Face OAuth2 (PKCE), engineered cloud asset and artifact storage pipelines across AWS (S3, EC2) , and designed Supabase PostgreSQL relational schemas and server-side RPCs for access code verification, quiz scoring, and deterministic chat logging.}
    \resumeItem{Used Python Pytest to test API endpoints, data validators, and database access paths, and wrote deployment documentation to help onboard researchers and student developers for hands-on development across semesters.}
    \resumeItem{Collaborated with SHIELD Lab faculty and other graduate researchers in iterative sprints, translating evolving requirements into executable tasks, code reviews, and shared runbooks for system maintenance.}
  \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed Java 11 and Spring Boot microservices for policy onboarding and validation with RESTful APIs, persisting client metadata in MongoDB and relational records in SQL Server, handling 20K+ peak hourly requests.}
    \resumeItem{Enhanced async validation workflows using CompletableFuture and ExecutorService for parallel task execution, improving request latency.}
    \resumeItem{Implemented multi-tier Redis caching with warm-up to reduce SQL Server load and improve p95 latency during peak onboarding traffic.}
    \resumeItem{Optimized audit and reporting queries using Spring Data JPA with Hibernate across PostgreSQL and SQL Server, eliminating N+1 patterns and reducing round trips.}
    \resumeItem{Refactored duplicate logic across 8+ microservices into reusable Spring Boot service-layer components with centralized exception handling and request validation.}
    \resumeItem{Implemented Spring Security OAuth2 with AWS Cognito, utilizing AWS cloud infrastructure (EC2, S3, RDS) for policy record management, and securing REST endpoints with JWT authentication and RBAC.}
    \resumeItem{Developed JUnit 5 and Mockito suites covering business-critical workflows, achieving 70\% coverage while reducing regressions.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida, Tampa}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\resumeSubHeadingListEnd

\section{CERTIFICATIONS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    AWS Certified AI Practitioner (AIF-C01) - Amazon Web Services (AWS) \\[1pt]
    Claude Certified Prompt Engineer - Anthropic \\[1pt]
    AWS Certified Cloud Practitioner - Amazon Web Services (AWS)
  }}
\end{itemize}

\end{document}
"""

# ==============================================================================
# 2. NODE STACK ARCHETYPE (TarunMannava_SE.docx)
# ==============================================================================
NODE_TEX = LATEX_PREAMBLE + r"""\newcommand{\resumeHeadingContact}{%
  Seattle, WA \hspace{0.4em}\resumeSep\hspace{0.4em}+1 (656) 203-7074 \hspace{0.4em}\resumeSep\hspace{0.4em}\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://github.com/tarunmannava}{GitHub}%
}

\begin{document}

\begin{center}
  {\Huge \textbf{TARUN MANNAVA}} \\[4pt]
  \small
  \resumeHeadingContact
\end{center}

\vspace{-10pt}

\section{SUMMARY}
AI \& Software Engineer with 4+ years of experience engineering scalable backend services and production agentic AI systems across Node.js, Python, and AWS. Specializing in multi-agent orchestration (Claude Code, LangGraph, CrewAI, AWS Bedrock), Model Context Protocol (MCP) server development, and SDLC developer productivity tooling. Proven expertise in building custom agent harnesses, enterprise API integrations, human-in-the-loop workflows, LLM observability (LangSmith, CloudWatch), and cost and telemetry controls.

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    \textbf{GenAI \& Agents:} Multi-Agent Workflows, Claude Code, AWS Bedrock, AgentCore, CrewAI, LangGraph, Model Context Protocol (MCP), Tool Calling, Agentic RAG, Corrective RAG, Human-in-the-Loop, Prompt Engineering \\[1pt]
    \textbf{LLMOps \& Governance:} LangSmith (Tracing, Evals, Datasets), RAGAS, LLM-as-Judge, AI Security \& Governance, Telemetry \& Cost Controls, Grounding Gates, Latency Tracking \\[1pt]
    \textbf{Languages:} TypeScript, JavaScript (Node.js), Python, SQL, Java \\[1pt]
    \textbf{Backend \& Tooling:} Node.js, Express.js, NestJS, FastAPI, REST APIs, WebSockets, CLI Tooling, Custom Developer Harnesses, Microservices, Asynchronous Event Loops, Pydantic, Prisma ORM \\[1pt]
    \textbf{Cloud \& AWS:} AWS Bedrock, Lambda, EC2, S3, RDS, Cognito, CloudWatch, API Gateway, Docker, Kubernetes, Linux, GitHub Actions, Redis, RabbitMQ \\[1pt]
    \textbf{Retrieval \& Data:} PostgreSQL (pgvector) / Supabase, Qdrant, Pinecone, SQL Server, MongoDB, HNSW Indexing, Dense \& Lexical Search, Reranking \\[1pt]
    \textbf{Testing \& Security:} OAuth2 PKCE, JWT, RBAC, Jest, Supertest, Pytest, JUnit 5, Mockito, SDLC Automation
  }}
\end{itemize}

\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{SkillBeacon: Skills \& Career Intelligence Platform $|$ \href{https://skillbeacon-six.vercel.app/}{\underline{Link}}}{Node.js, TypeScript, Next.js, React, Python, FastAPI, PostgreSQL, Cloudflare R2, Google OAuth2}
  \resumeItemListStart
    \resumeItem{Built a full-stack career platform with Node.js/TypeScript and Python/FastAPI backend microservices and React/Next.js frontend, supporting multi-role student, mentor, and employer workflows with PostgreSQL and Prisma ORM persistence.}
    \resumeItem{Implemented Skill Passport with skill proficiency tiers, evidence submissions, and multi-party confidence scoring algorithms based on mentor and employer verification signals.}
    \resumeItem{Architected an automated job intelligence engine with Next.js SSR data scraping, persistent CSV/JSON deduplication, and an intelligent soft-flagging system for qualification filtering.}
    \resumeItem{Engineered an asynchronous document generation microservice in FastAPI to dynamically tailor LaTeX templates and compile clean, ATS-compliant DOCX resumes under 2s latency.}
  \resumeItemListEnd

  \resumeProject{AutoDocs: Event-Driven MCP \& Multi-Agent Documentation System}{Node.js, TypeScript, Python, FastAPI, MCP, LangGraph, RabbitMQ, WebSockets, Supabase, GitHub Webhooks, LangSmith}
  \resumeItemListStart
    \resumeItem{Built an event-driven developer productivity and SDLC documentation platform receiving GitHub PR webhooks, validating HMAC-SHA256 signatures and enforcing idempotent delivery persistence in Supabase.}
    \resumeItem{Implemented asynchronous job processing with RabbitMQ, decoupling webhook ingestion from repository AST analysis and long-running documentation workflows with retry and failure handling.}
    \resumeItem{Designed custom Model Context Protocol (MCP) code-intelligence servers using AST analysis to extract class and function call graphs, providing structural codebase context to LLMs.}
    \resumeItem{Architected dynamic task-routing multi-agent workflows with LangGraph and Claude Code developer harnesses to analyze code diffs and generate contextual documentation with deterministic verification guardrails.}
  \resumeItemListEnd

  \resumeProject{JobPilot: Conversational Job-Search \& Ranking Agent}{Python, LangGraph, LangChain, MCP, Dice MCP, LangSmith, Human-in-the-Loop}
  \resumeItemListStart
    \resumeItem{Built a conversational agent that extracts user resume criteria and job preferences through natural-language dialogue, enforcing human-in-the-loop confirmation before executing downstream searches.}
    \resumeItem{Integrated the Dice Model Context Protocol (MCP) server as a tool-use client to retrieve live job listings, validating tool schemas and handling graceful fallbacks.}
    \resumeItem{Implemented an agentic resume-to-listing ranking step scoring and prioritizing retrieved opportunities against parsed resumes and candidate constraints.}
    \resumeItem{Instrumented end-to-end LLM observability with LangSmith tracing and pass/fail evaluation on tool-call correctness, tracking latency, token cost, and routing fidelity per run.}
  \resumeItemListEnd

  \resumeProject{FinScope: Hierarchical Earnings Intelligence Graph}{Python, LangGraph, LangChain, SEC-API, Tavily, LangSmith, Human-in-the-Loop}
  \resumeItemListStart
    \resumeItem{Built a hierarchical multi-agent system for earnings analysis that routes filings through specialized analyst nodes, synthesizing ratio analysis and risk review into a structured investment memo.}
    \resumeItem{Implemented LangGraph supervisor-worker routing with shared Pydantic financial state, delegating fetch, calculation, and review steps across isolated nodes with conditional edges for low-confidence escalation.}
    \resumeItem{Integrated SEC-API and Tavily web search as LangChain tool nodes to retrieve live filings and market context, adding numeric validation to block incorrect calculations before synthesis.}
    \resumeItem{Implemented human-approval interrupt that pauses execution for analyst review when confidence scores fall below threshold, with checkpointed state for resume and audit.}
  \resumeItemListEnd

  \resumeProject{ProofStack: MCP-Backed Corrective Retrieval Graph}{Python, Node.js, FastAPI, LangGraph, MCP Protocol, PostgreSQL (pgvector), Tavily, LangSmith}
  \resumeItemListStart
    \resumeItem{Built a corrective RAG system that answers questions over internal docs by routing all retrieval through MCP tool servers, falling back to web search only when graded evidence is insufficient.}
    \resumeItem{Implemented LangGraph retrieve-grade-rewrite loop that rewrites ambiguous queries, retrieves via MCP tools, grades document relevance, and regenerates answers until grounding threshold is met.}
    \resumeItem{Designed three Model Context Protocol servers as LangChain tools: vector\_search over PostgreSQL (pgvector HNSW) with dense-lexical hybrid ranking, docs\_sql for structured records, and web\_search via Tavily.}
    \resumeItem{Architected verification guardrails with grounding-score gates and Pydantic-validated RAG state, instrumenting full LLM observability with LangSmith tracing per-route cost and latency.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EXPERIENCE}
\resumeSubHeadingListStart

  \resumeSubheading
    {University of South Florida}{Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Architected and maintained a production AI \& Health Literacy web platform for the USF SHIELD Lab across 13 interactive modules (serving 60+ biomedical students and faculty), engineering Node.js and TypeScript backend microservices with Express and Prisma ORM.}
    \resumeItem{Engineered a real-time dual-model LLM sandbox backend in Node.js integrating AWS Bedrock and Hugging Face APIs with WebSocket/Socket.io streaming, semantic evaluation rubrics, and Redis caching that keeps response latency below 2 seconds.}
    \resumeItem{Implemented an in-browser prompt evaluation engine using Transformers.js (WASM/ONNX) to compute cosine-similarity embedding scoring locally, delivering zero-latency, privacy-preserving feedback on prompt constraints and structure.}
    \resumeItem{Built authentication and session management with OAuth2 (PKCE), engineered cloud-native asset storage and telemetry pipelines on AWS (S3, EC2, CloudWatch), and designed Supabase PostgreSQL relational schemas and server-side RPCs for deterministic chat logging and quiz scoring.}
    \resumeItem{Developed automated test suites using Jest and Supertest for Node.js API endpoints and database access paths, creating custom CLI developer harnesses and CI/CD workflows to accelerate module testing and deployment.}
    \resumeItem{Collaborated with SHIELD Lab faculty and researchers in iterative agile sprints, establishing AI security guardrails, prompt evaluation rubrics, code reviews, and shared operational runbooks for system maintenance.}
  \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed Java 11 and Spring Boot microservices for policy onboarding and validation with RESTful APIs, persisting client metadata in MongoDB and relational records in SQL Server, handling 20K+ peak hourly requests.}
    \resumeItem{Enhanced async validation workflows using CompletableFuture and ExecutorService for parallel task execution, improving request latency.}
    \resumeItem{Implemented multi-tier Redis caching with warm-up to reduce SQL Server load and improve p95 latency during peak onboarding traffic.}
    \resumeItem{Optimized audit and reporting queries using Spring Data JPA with Hibernate across PostgreSQL and SQL Server, eliminating N+1 patterns and reducing round trips.}
    \resumeItem{Refactored duplicate logic across 8+ microservices into reusable Spring Boot service-layer components with centralized exception handling and request validation.}
    \resumeItem{Implemented Spring Security OAuth2 with AWS Cognito, utilizing AWS cloud infrastructure (EC2, S3, RDS) for policy record management, and securing REST endpoints with JWT authentication and RBAC.}
    \resumeItem{Developed JUnit 5 and Mockito suites covering business-critical workflows, achieving 70\% coverage while reducing regressions.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida, Tampa}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\resumeSubHeadingListEnd

\section{CERTIFICATIONS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    AWS Certified AI Practitioner (AIF-C01) - Amazon Web Services (AWS) \\[1pt]
    Claude Certified Prompt Engineer - Anthropic \\[1pt]
    AWS Certified Cloud Practitioner - Amazon Web Services (AWS)
  }}
\end{itemize}

\end{document}
"""

# ==============================================================================
# 3. JAVA STACK ARCHETYPE (TarunMannava_SoftwareEngineer.docx)
# ==============================================================================
JAVA_TEX = LATEX_PREAMBLE + r"""\newcommand{\resumeHeadingContact}{%
  Seattle, WA \hspace{0.4em}\resumeSep\hspace{0.4em}+1 (656) 203-7074 \hspace{0.4em}\resumeSep\hspace{0.4em}\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://github.com/tarunmannava}{GitHub}%
}

\begin{document}

\begin{center}
  {\Huge \textbf{Tarun Mannava}} \\[4pt]
  \small
  \resumeHeadingContact \\[4pt]
  \textit{Full Stack Software Engineer with 3+ years of experience building high throughput microservices in Java 11/17 and Spring Boot alongside responsive React/TypeScript frontends. Proven track record in relational and NoSQL database optimization (PostgreSQL, MongoDB, SQL Server), event-driven messaging with RabbitMQ, and architecting AI solutions with AI-in-the-loop validation and custom AI skills.}
\end{center}

\vspace{-10pt}

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    \textbf{Languages:} Java (11/17/21), SQL, Python, JavaScript, TypeScript \\[1pt]
    \textbf{Backend \& Frameworks:} Spring Boot, Spring MVC, Spring Security, Spring Data JPA, Hibernate, FastAPI, REST APIs, Microservices \\[1pt]
    \textbf{AI Developer Tools \& GenAI:} Claude Code, Cursor, GitHub Copilot, LLMs, RAG, LangGraph, LangChain, Multi-Agent Systems, Model Context Protocol (MCP), Prompt Engineering \\[1pt]
    \textbf{Messaging \& Distributed Systems:} RabbitMQ, Redis, CompletableFuture, Asynchronous Processing, Event-Driven Architecture \\[1pt]
    \textbf{Databases \& Cloud:} PostgreSQL, MongoDB, SQL Server, AWS, GCP, Azure, Cloudflare R2, Docker, Linux, GitHub Actions, jOOQ \\[1pt]
    \textbf{Testing \& Frontend:} JUnit 5, Mockito, Pytest, Postman, React, HTML5, CSS3
  }}
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart

  \resumeSubheading
    {University of South Florida}{Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Prototyped a Behavioral Health Workflow Platform supporting session tracking, therapist workflows, and clinic resource utilization for behavioral health services.}
    \resumeItem{Engineered Java 17 and Spring Boot microservices to model therapist productivity, billable vs. non-billable hours, session activity, and physical room utilization across daily, weekly, and monthly reporting periods.}
    \resumeItem{Built PostgreSQL data pipelines using jOOQ to organize session and operational data for utilization and financial analysis.}
    \resumeItem{Implemented AWS Cognito and PostgreSQL synchronization for role-based access, therapist accounts, and administrator profiles within the prototype.}
    \resumeItem{Designed session lifecycle workflows with state transitions, automated status restoration, granular session activity auditing, and Excel-based data exports using Apache POI.}
    \resumeItem{Built React 18 and TypeScript dashboards with utilization metrics, Recharts trend visualizations, custom date ranges reporting.}
    \resumeItem{Developed JUnit 5 and Mockito test suites to validate backend workflows, data processing, and session state transitions.}
  \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed Java 11 and Spring Boot microservices for policy onboarding and validation with RESTful APIs, persisting client metadata in MongoDB and relational records in SQL Server, contributing to high-throughput healthcare platform handling 20K+ peak hourly requests.}
    \resumeItem{Enhanced asynchronous validation workflows using CompletableFuture and ExecutorService for parallel task execution, improving request latency.}
    \resumeItem{Implemented multi-tier Redis caching strategies with cache warm-up mechanisms to reduce SQL Server load and improve p95 API response latency during peak onboarding traffic.}
    \resumeItem{Optimized policy audit and reporting queries using Spring Data JPA with Hibernate across PostgreSQL and SQL Server, eliminating N+1 query patterns and reducing database round trips.}
    \resumeItem{Refactored duplicate business logic across 8+ microservices into reusable Spring Boot service-layer components with centralized exception handling and Spring MVC request validation.}
    \resumeItem{Implemented Spring Security OAuth2 integration with AWS Cognito, securing REST endpoints with JWT-based authentication and role-based access control for enterprise IAM.}
    \resumeItem{Developed comprehensive JUnit 5 and Mockito test suites covering business-critical workflows, achieving 70\% backend code coverage while reducing production regressions.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{SkillBeacon -- Skills \& Career Intelligence Platform $|$ \href{https://skillbeacon-six.vercel.app/}{\underline{Link}}}{Python, FastAPI, React, PostgreSQL, Cloudflare R2, Google OAuth2, Gmail API, Neon Auth}
  \resumeItemListStart
    \resumeItem{Built a full-stack career platform with a Python/FastAPI backend and React frontend, supporting multi-role student, mentor, and employer workflows with PostgreSQL and SQLAlchemy ORM persistence.}
    \resumeItem{Implemented Skill Passport with skill proficiency tiers, evidence submissions, and multi-party confidence scoring algorithms based on mentor and employer verification signals.}
    \resumeItem{Architected an automated job intelligence engine with Next.js SSR data scraping, persistent CSV/JSON deduplication, and an intelligent soft-flagging system for qualification filtering.}
    \resumeItem{Engineered an asynchronous document generation microservice in FastAPI to dynamically tailor LaTeX templates and compile clean, ATS-compliant DOCX resumes under 2s latency.}
    \resumeItem{Integrated Google OAuth 2.0 with the Gmail REST API, building a scheduled background daemon that dispatches responsive, mobile-first multipart HTML email digests with direct application links.}
    \resumeItem{Integrated Cloudflare R2 via its S3-compatible API for resumes, logos, and evidence files, implementing presigned downloads, storage quotas, and Neon Auth JWT role-based access controls.}
  \resumeItemListEnd

  \resumeProject{AutoDocs -- Event-Driven MCP \& Multi-Agent Documentation System}{Python, FastAPI, MCP Protocol, A2A Protocol, RabbitMQ, Supabase, GitHub Webhooks}
  \resumeItemListStart
    \resumeItem{Built an event-driven documentation system receiving pull-request webhooks via FastAPI, validating GitHub HMAC-SHA256 signatures, and enforcing idempotent delivery persistence in Supabase.}
    \resumeItem{Implemented asynchronous job processing with RabbitMQ, separating webhook ingestion from repository analysis and long-running documentation workflows with retry and failure handling.}
    \resumeItem{Designed Model Context Protocol (MCP) AST code intelligence servers extracting class and function call graphs to provide structural repository context to LLMs.}
    \resumeItem{Architected dynamic task-routing multi-agent systems using LangGraph to analyze code changes and generate contextual documentation with deterministic verification guardrails.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\resumeSubHeadingListEnd

\section{CERTIFICATIONS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    AWS Certified Cloud Practitioner -- Amazon, Nov 2023 \\[1pt]
    Google Cloud Certified: Associate Cloud Engineer -- Google \\[1pt]
    Microsoft Certified: Azure Fundamentals (AZ-900) -- Microsoft
  }}
\end{itemize}

\end{document}
"""

# ==============================================================================
# 4. DOTNET STACK ARCHETYPE (TarunMannava_DotnetDeveloper.docx)
# ==============================================================================
DOTNET_TEX = LATEX_PREAMBLE + r"""\newcommand{\resumeHeadingContact}{%
  Tampa, FL \hspace{0.4em}\resumeSep\hspace{0.4em}+1 (656) 203-7074 \hspace{0.4em}\resumeSep\hspace{0.4em}\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://github.com/tarunmannava}{GitHub}%
}

\begin{document}

\begin{center}
  {\Huge \textbf{Tarun Mannava}} \\[4pt]
  \small
  \resumeHeadingContact \\[4pt]
  \textit{Full Stack Software Engineer with 3+ years of experience specializing in C\#, .NET 8 / ASP.NET Core, and distributed systems alongside modern React frontends. Experienced in enterprise Web APIs, Entity Framework Core optimization, SQL Server architectures, and architecting AI-in-the-loop solutions integrating custom AI skills and automated evaluation pipelines.}
\end{center}

\vspace{-10pt}

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    \textbf{Languages \& Core:} C\#, .NET 8 / .NET Core, ASP.NET Core, Entity Framework Core, LINQ, SQL, Python, TypeScript, JavaScript \\[1pt]
    \textbf{Backend \& APIs:} RESTful APIs, Web API, Microservices, FastAPI, RabbitMQ, Redis Caching, OAuth2, JWT \\[1pt]
    \textbf{AI Developer Tools \& GenAI:} Claude Code, Cursor, GitHub Copilot, LLMs, RAG, LangGraph, LangChain, Multi-Agent Systems, Model Context Protocol (MCP), Prompt Engineering \\[1pt]
    \textbf{Databases \& Cloud:} SQL Server (T-SQL), PostgreSQL, MongoDB, AWS, Cloudflare R2, Docker, Linux, GitHub Actions, CI/CD \\[1pt]
    \textbf{Testing \& Frontend:} xUnit, NUnit, Moq, Pytest, Postman, React, HTML5, CSS3
  }}
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart

  \resumeSubheading
    {University of South Florida}{Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Prototyped a Behavioral Health Workflow Platform supporting session tracking, therapist workflows, and clinic resource utilization for behavioral health services.}
    \resumeItem{Engineered C\# and .NET 8 microservices to model therapist productivity, billable vs. non-billable hours, session activity, and physical room utilization across daily, weekly, and monthly reporting periods.}
    \resumeItem{Built PostgreSQL data pipelines using Entity Framework Core and LINQ to organize session and operational data for utilization and financial analysis.}
    \resumeItem{Implemented AWS Cognito and PostgreSQL synchronization for role-based access, therapist accounts, and administrator profiles within the prototype.}
    \resumeItem{Designed session lifecycle workflows with state transitions, automated status restoration, granular session activity auditing, and Excel-based data exports using ClosedXML.}
    \resumeItem{Built React 18 and TypeScript dashboards with utilization metrics, Recharts trend visualizations, and custom date-range reporting.}
    \resumeItem{Developed xUnit and Moq test suites to validate backend workflows, data processing, and session state transitions.}
  \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed C\# / .NET 8 / ASP.NET Core microservices for policy onboarding and validation with RESTful APIs, persisting client metadata in MongoDB and relational records in SQL Server, supporting high-throughput platform handling 20K+ peak hourly requests.}
    \resumeItem{Enhanced asynchronous validation workflows built with async/await and Task Parallel Library (TPL) for parallel task execution, improving transaction request latency.}
    \resumeItem{Implemented Redis distributed caching strategies and cache warm-up mechanisms, reducing SQL Server load and improving p95 API response latency by 30\% during peak onboarding traffic.}
    \resumeItem{Optimized policy audit and reporting queries using Entity Framework Core, LINQ, and SQL across PostgreSQL and SQL Server, eliminating N+1 query patterns and reducing database round trips.}
    \resumeItem{Contributed to refactoring duplicate business logic across 8+ microservices into reusable ASP.NET Core service-layer components with centralized exception handling and API validation.}
    \resumeItem{Implemented ASP.NET Core authentication with OAuth2 and JWT integration with AWS Cognito by adding new authorization features and securing REST endpoints.}
    \resumeItem{Developed automated unit and integration test suites with xUnit, NUnit, and Moq covering business-critical workflows, achieving 70\% backend code coverage while reducing production regressions.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{SkillBeacon -- Skills \& Career Intelligence Platform $|$ \href{https://skillbeacon-six.vercel.app/}{\underline{Link}}}{Python, FastAPI, React, PostgreSQL, Cloudflare R2, Google OAuth2, Gmail API, Neon Auth}
  \resumeItemListStart
    \resumeItem{Built a full-stack career platform with a Python/FastAPI backend and React frontend, supporting multi-role student, mentor, and employer workflows with PostgreSQL and SQLAlchemy ORM persistence.}
    \resumeItem{Implemented Skill Passport with skill proficiency tiers, evidence submissions, and multi-party confidence scoring algorithms based on mentor and employer verification signals.}
    \resumeItem{Architected an automated job intelligence engine with Next.js SSR data scraping, persistent CSV/JSON deduplication, and an intelligent soft-flagging system for qualification filtering.}
    \resumeItem{Engineered an asynchronous document generation microservice in FastAPI to dynamically tailor LaTeX templates and compile clean, ATS-compliant DOCX resumes under 2s latency.}
    \resumeItem{Integrated Google OAuth 2.0 with the Gmail REST API, building a scheduled background daemon that dispatches responsive, mobile-first multipart HTML email digests with direct application links.}
    \resumeItem{Integrated Cloudflare R2 via its S3-compatible API for resumes, logos, and evidence files, implementing presigned downloads, storage quotas, and Neon Auth JWT role-based access controls.}
  \resumeItemListEnd

  \resumeProject{AutoDocs -- Event-Driven MCP \& Multi-Agent Documentation System}{Python, FastAPI, MCP Protocol, A2A Protocol, RabbitMQ, Supabase, GitHub Webhooks}
  \resumeItemListStart
    \resumeItem{Built an event-driven documentation system receiving pull-request webhooks via FastAPI, validating GitHub HMAC-SHA256 signatures, and enforcing idempotent delivery persistence in Supabase.}
    \resumeItem{Implemented asynchronous job processing with RabbitMQ, separating webhook ingestion from repository analysis and long-running documentation workflows with retry and failure handling.}
    \resumeItem{Designed Model Context Protocol (MCP) AST code intelligence servers extracting class and function call graphs to provide structural repository context to LLMs.}
    \resumeItem{Architected dynamic task-routing multi-agent systems using LangGraph to analyze code changes and generate contextual documentation with deterministic verification guardrails.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\resumeSubHeadingListEnd

\end{document}
"""

# ==============================================================================
# 5. PYTHON STACK ARCHETYPE (TarunMannava_SoftwareDeveloper.docx)
# ==============================================================================
PYTHON_TEX = LATEX_PREAMBLE + r"""\newcommand{\resumeHeadingContact}{%
  Tampa, FL \hspace{0.4em}\resumeSep\hspace{0.4em}+1 (656) 203-7074 \hspace{0.4em}\resumeSep\hspace{0.4em}\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://github.com/tarunmannava}{GitHub}%
}

\begin{document}

\begin{center}
  {\Huge \textbf{Tarun Mannava}} \\[4pt]
  \small
  \resumeHeadingContact \\[4pt]
  \textit{Full Stack Software Developer with 3+ years of experience building asynchronous backend microservices in Python 3.10+, FastAPI, and React frontends. Proven expertise in relational/NoSQL data modeling (SQLAlchemy, PostgreSQL, MongoDB), background task pipelines with RabbitMQ and Redis, and architecting production AI solutions with AI-in-the-loop workflows.}
\end{center}

\vspace{-10pt}

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \small{\item{
    \textbf{Languages:} Python (3.10+), SQL, Java, TypeScript, JavaScript, Bash \\[1pt]
    \textbf{Backend \& APIs:} FastAPI, Flask, Django, Pydantic, AsyncIO, SQLAlchemy, REST APIs, Microservices, Spring Boot \\[1pt]
    \textbf{AI Developer Tools \& GenAI:} Claude Code, Cursor, GitHub Copilot, LLMs, RAG, LangGraph, LangChain, Multi-Agent Systems, Model Context Protocol (MCP), Prompt Engineering \\[1pt]
    \textbf{Messaging \& Distributed Systems:} RabbitMQ, Redis, Asynchronous Processing, Event-Driven Architecture \\[1pt]
    \textbf{Databases \& Cloud:} PostgreSQL, MongoDB, SQL Server, AWS, Cloudflare R2, Docker, Linux, GitHub Actions, CI/CD \\[1pt]
    \textbf{Testing \& Frontend:} pytest, unittest, JUnit, Postman, React, Next.js, HTML5, CSS3
  }}
\end{itemize}

\section{EXPERIENCE}
\resumeSubHeadingListStart

  \resumeSubheading
    {University of South Florida}{Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Architected and deployed a production AI \& Health Literacy platform across 13 interactive modules in React, TypeScript, and Python 3.10+ FastAPI/AsyncIO (serving 60+ biomedical students/faculty), engineering PostgreSQL relational schemas with SQLAlchemy and Hugging Face OAuth2 (PKCE) authentication.}
    \resumeItem{Engineered a real-time dual-model sandbox integrating Groq and Hugging Face LLM APIs with AsyncIO concurrency and Pydantic validation for milestone detection and semantic grading rubrics under 2s latency.}
    \resumeItem{Built an in-browser prompt evaluation engine using Transformers.js (WASM / ONNX) for local cosine similarity embedding scoring with Pydantic schemas, delivering zero-latency pedagogical feedback.}
    \resumeItem{Developed a RAG-based clinical nutrition chatbot for MyFoodRx, implementing a multi-layer safety architecture with query classification, semantic filtering, and Redis/Gemini rate-limit-aware caching.}
  \resumeItemListEnd

  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed Java 11/Spring Boot microservices for policy onboarding and validation persisting client metadata in MongoDB, contributing to a high-throughput healthcare/insurance platform handling 20K+ hourly transactions.}
    \resumeItem{Enhanced asynchronous validation workflows built with CompletableFuture and ExecutorService, improving request latency through parallel task execution.}
    \resumeItem{Implemented Redis-backed caching strategies and cache warm-up mechanisms, reducing SQL Server load and improving p95 API response latency by 30\% during peak onboarding traffic.}
    \resumeItem{Optimized policy audit and reporting queries using jOOQ and SQL across PostgreSQL and SQL Server, eliminating N+1 query patterns and reducing database round trips.}
    \resumeItem{Contributed to refactoring duplicate business logic across 8+ microservices into reusable Spring service-layer components with centralized exception handling.}
    \resumeItem{Implemented Spring Security OAuth2 integration with AWS Cognito by adding new authorization features and securing REST endpoints with JWT-based authentication.}
    \resumeItem{Developed JUnit and Cucumber test suites covering business-critical workflows, achieving 70\% backend code coverage while reducing production regressions.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProject{SkillBeacon -- Skills \& Career Intelligence Platform $|$ \href{https://skillbeacon-six.vercel.app/}{\underline{Link}}}{Python, FastAPI, React, PostgreSQL, Cloudflare R2, Google OAuth2, Gmail API, Neon Auth}
  \resumeItemListStart
    \resumeItem{Built a full-stack career platform with a Python/FastAPI backend and React frontend, supporting multi-role student, mentor, and employer workflows with PostgreSQL and SQLAlchemy ORM persistence.}
    \resumeItem{Implemented Skill Passport with skill proficiency tiers, evidence submissions, and multi-party confidence scoring algorithms based on mentor and employer verification signals.}
    \resumeItem{Architected an automated job intelligence engine with Next.js SSR data scraping, persistent CSV/JSON deduplication, and an intelligent soft-flagging system for qualification filtering.}
    \resumeItem{Engineered an asynchronous document generation microservice in FastAPI to dynamically tailor LaTeX templates and compile clean, ATS-compliant DOCX resumes under 2s latency.}
    \resumeItem{Integrated Google OAuth 2.0 with the Gmail REST API, building a scheduled background daemon that dispatches responsive, mobile-first multipart HTML email digests with direct application links.}
    \resumeItem{Integrated Cloudflare R2 via its S3-compatible API for resumes, logos, and evidence files, implementing presigned downloads, storage quotas, and Neon Auth JWT role-based access controls.}
  \resumeItemListEnd

  \resumeProject{AutoDocs -- Event-Driven MCP \& Multi-Agent Documentation System}{Python, FastAPI, MCP Protocol, A2A Protocol, RabbitMQ, Supabase, GitHub Webhooks}
  \resumeItemListStart
    \resumeItem{Built an event-driven documentation system receiving pull-request webhooks via FastAPI, validating GitHub HMAC-SHA256 signatures, and enforcing idempotent delivery persistence in Supabase.}
    \resumeItem{Implemented asynchronous job processing with RabbitMQ, separating webhook ingestion from repository analysis and long-running documentation workflows with retry and failure handling.}
    \resumeItem{Designed Model Context Protocol (MCP) AST code intelligence servers extracting class and function call graphs to provide structural repository context to LLMs.}
    \resumeItem{Architected dynamic task-routing multi-agent systems using LangGraph to analyze code changes and generate contextual documentation with deterministic verification guardrails.}
  \resumeItemListEnd

\resumeSubHeadingListEnd

\section{EDUCATION}
\resumeSubHeadingListStart
  \resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\resumeSubHeadingListEnd

\end{document}
"""

archetypes = {
    "ai": AI_TEX,
    "node": NODE_TEX,
    "java": JAVA_TEX,
    "dotnet": DOTNET_TEX,
    "python": PYTHON_TEX,
}

for name, content in archetypes.items():
    tex_path = ARCHETYPES_DIR / f"{name}.tex"
    docx_path = ARCHETYPES_DIR / f"{name}.docx"
    tex_path.write_text(content.strip(), encoding="utf-8")
    print(f"Wrote {tex_path.name} ({len(content)} chars)")
    convert_tex_to_docx(tex_path, docx_path)
    print(f"Compiled {docx_path.name} ({docx_path.stat().st_size} bytes)")

print("\nAll 5 archetypes written and compiled to docx successfully.")
