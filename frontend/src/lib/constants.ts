export const sampleResume = `%-------------------------
% Tarun Mannava - Resume in LaTeX
% ATS-Friendly Resume Template
%-------------------------

\\documentclass[a4paper,10pt]{article}

\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage{latexsym}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[hidelinks]{hyperref}
\\usepackage{fancyhdr}
\\usepackage[english]{babel}
\\usepackage{tabularx}
\\usepackage{mathptmx}
\\usepackage{geometry}
\\usepackage{setspace}
\\usepackage{anyfontsize}

% Standardized thin margins to maximize space safely
\\geometry{
  a4paper,
  top=0.35in,
  bottom=0.35in,
  left=0.4in,
  right=0.4in
}

\\setstretch{1.0}
\\renewcommand{\\normalsize}{\\fontsize{10}{12}\\selectfont}
\\renewcommand{\\small}{\\fontsize{10}{12}\\selectfont}
\\normalsize

\\pagestyle{fancy}
\\fancyhf{}
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

\\urlstyle{same}
\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}

% Section title formatting
\\titleformat{\\section}{
  \\vspace{-10pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-7pt}]

\\newcommand{\\resumeSep}{\\textbullet}

\\newcommand{\\resumeItem}[1]{
  \\item\\small{#1}
}

% Experience / education: stacked lines parse cleanly in PDF-to-text
\\newcommand{\\resumeSubheading}[4]{%
  \\vspace{0pt}\\item
  \\textbf{#1} \\\\
  \\textit{\\small #2} \\\\
  \\small #3 -- #4
  \\vspace{2pt}
}

% Projects: 2 arguments (Title, Tech Stack)
\\newcommand{\\resumeProject}[2]{%
  \\vspace{0pt}\\item[]
  \\textbf{#1} \\\\
  \\small\\textit{#2}
  \\vspace{2pt}
}

\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]}
\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}

\\newcommand{\\resumeItemListStart}{%
  \\begin{itemize}[leftmargin=0.15in, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt, label={$\\bullet$}]%
}
\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{2pt}}

\\newcommand{\\resumeHeadingContact}{%
  Tampa, FL \\hspace{0.4em}\\resumeSep\\hspace{0.4em}+1 (656) 203-7074 \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{https://github.com/tarunmannava}{GitHub}%
}

%-------------------------------------------
\\begin{document}

%---------- HEADING ----------
\\begin{center}
  {\\Huge \\textbf{Tarun Mannava}} \\\\[4pt]
  \\small
  \\resumeHeadingContact \\\\[4pt]
  \\textit{Full Stack Software Engineer with 3+ years of experience building high-throughput microservices in Java 11/17 and Spring Boot alongside responsive React/TypeScript frontends. Proven track record in relational and NoSQL database optimization (PostgreSQL, MongoDB, SQL Server), event-driven messaging with RabbitMQ, and architecting AI solutions with AI-in-the-loop validation and custom AI skills.}
\\end{center}

\\vspace{-10pt}

%---------- SKILLS ----------
\\section{SKILLS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{Languages:} Java (11/17/21), SQL, Python, JavaScript, TypeScript \\\\[1pt]
    \\textbf{Backend \\& Frameworks:} Spring Boot, Spring MVC, Spring Security, Spring Data JPA, Hibernate, FastAPI, REST APIs, Microservices \\\\[1pt]
    \\textbf{AI Developer Tools \\& GenAI:} Claude Code, Cursor, GitHub Copilot, LLMs, RAG, LangGraph, LangChain, Multi-Agent Systems, Model Context Protocol (MCP), Prompt Engineering \\\\[1pt]
    \\textbf{Messaging \\& Distributed Systems:} RabbitMQ, Redis, CompletableFuture, Asynchronous Processing, Event-Driven Architecture \\\\[1pt]
    \\textbf{Databases \\& Cloud:} PostgreSQL, MongoDB, SQL Server, AWS, Cloudflare R2, Docker, Linux, GitHub Actions, jOOQ \\\\[1pt]
    \\textbf{Testing \\& Frontend:} JUnit 5, Mockito, Pytest, Postman, React, HTML5, CSS3
  }}
\\end{itemize}

%---------- EXPERIENCE ----------
\\section{EXPERIENCE}
\\resumeSubHeadingListStart

  \\resumeSubheading
    {University of South Florida}{Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \\resumeItemListStart
    \\resumeItem{Architected and deployed a production AI \\& Health Literacy web platform across 13 interactive modules in React and TypeScript (serving 60+ biomedical students/faculty), engineering PostgreSQL relational schemas with Spring Data JPA/Hibernate and OAuth2 (PKCE) authentication.}
    \\resumeItem{Engineered a Java 17 and Spring Boot microservice backend with a real-time dual-model sandbox integrating Groq and Hugging Face LLM APIs for milestone detection and automated semantic rubric evaluation under 2s latency.}
    \\resumeItem{Built an in-browser evaluation engine using Transformers.js (WASM / ONNX) and TypeScript for local cosine similarity embedding scoring, delivering zero-latency pedagogical feedback.}
    \\resumeItem{Developed a RAG-based clinical nutrition chatbot for MyFoodRx, implementing a multi-layer safety architecture with query classification, semantic filtering, and rate-limit-aware caching using Google Gemini.}
  \\resumeItemListEnd

  \\resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \\resumeItemListStart
    \\resumeItem{Developed Java 11 and Spring Boot microservices for policy onboarding and validation with RESTful APIs, persisting client metadata in MongoDB and relational records in SQL Server, contributing to high-throughput healthcare platform handling 20K+ peak hourly requests.}
    \\resumeItem{Enhanced asynchronous validation workflows using CompletableFuture and ExecutorService for parallel task execution, improving request latency.}
    \\resumeItem{Implemented multi-tier Redis caching strategies with cache warm-up mechanisms to reduce SQL Server load and improve p95 API response latency during peak onboarding traffic.}
    \\resumeItem{Optimized policy audit and reporting queries using jOOQ and Spring Data JPA with Hibernate across PostgreSQL and SQL Server, eliminating N+1 query patterns and reducing database round trips.}
    \\resumeItem{Refactored duplicate business logic across 8+ microservices into reusable Spring Boot service-layer components with centralized exception handling and Spring MVC request validation.}
    \\resumeItem{Implemented Spring Security OAuth2 integration with AWS Cognito, securing REST endpoints with JWT-based authentication and role-based access control for enterprise IAM.}
    \\resumeItem{Developed comprehensive JUnit 5 and Mockito test suites covering business-critical workflows, achieving 70\\% backend code coverage while reducing production regressions.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- PROJECTS ----------
\\section{PROJECTS}
\\resumeSubHeadingListStart

  \\resumeProject{SkillBeacon -- Skills \\& Career Intelligence Platform $|$ \\href{https://skillbeacon-six.vercel.app/}{\\underline{Link}}}{Python, FastAPI, React, PostgreSQL, Cloudflare R2, Google OAuth2, Gmail API, Neon Auth}
  \\resumeItemListStart
    \\resumeItem{Built a full-stack career platform with a Python/FastAPI backend and React frontend, supporting multi-role student, mentor, and employer workflows with PostgreSQL and SQLAlchemy ORM persistence.}
    \\resumeItem{Implemented Skill Passport with skill proficiency tiers, evidence submissions, and multi-party confidence scoring algorithms based on mentor and employer verification signals.}
    \\resumeItem{Architected an automated job intelligence engine with Next.js SSR data scraping, persistent CSV/JSON deduplication, and an intelligent soft-flagging system for qualification filtering.}
    \\resumeItem{Engineered an asynchronous document generation microservice in FastAPI to dynamically tailor LaTeX templates and compile clean, ATS-compliant DOCX resumes under 2s latency.}
    \\resumeItem{Integrated Google OAuth 2.0 with the Gmail REST API, building a scheduled background daemon that dispatches responsive, mobile-first multipart HTML email digests with direct application links.}
    \\resumeItem{Integrated Cloudflare R2 via its S3-compatible API for resumes, logos, and evidence files, implementing presigned downloads, storage quotas, and Neon Auth JWT role-based access controls.}
  \\resumeItemListEnd

  \\resumeProject{AutoDocs -- Event-Driven MCP \\& Multi-Agent Documentation System}{Python, FastAPI, MCP Protocol, A2A Protocol, RabbitMQ, Supabase, GitHub Webhooks}
  \\resumeItemListStart
    \\resumeItem{Built an event-driven documentation system receiving pull-request webhooks via FastAPI, validating GitHub HMAC-SHA256 signatures, and enforcing idempotent delivery persistence in Supabase.}
    \\resumeItem{Implemented asynchronous job processing with RabbitMQ, separating webhook ingestion from repository analysis and long-running documentation workflows with retry and failure handling.}
    \\resumeItem{Designed Model Context Protocol (MCP) AST code intelligence servers extracting class and function call graphs to provide structural repository context to LLMs.}
    \\resumeItem{Architected dynamic task-routing multi-agent systems using LangGraph to analyze code changes and generate contextual documentation with deterministic verification guardrails.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- EDUCATION ----------
\\section{EDUCATION}
\\resumeSubHeadingListStart
  \\resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\\resumeSubHeadingListEnd

%-------------------------------------------
\\end{document}`;
