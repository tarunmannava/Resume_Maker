import re
import logging
from pathlib import Path
from google import genai
from google.genai import types
from openai import OpenAI

from ..core.config import get_settings
from ..models.schemas import RewriteRequest, RewriteResponse
from .keyword_extractor import extract_keywords
from .latex import latex_to_text, sanitize_latex_escaping
from .scoring import HIGH_RISK_DIRECT_SUBSTITUTIONS, score_keywords
from .job_analyzer import detect_target_stack, detect_details_with_keywords

logger = logging.getLogger("uvicorn.error")


SYSTEM_PROMPT_BASE = r"""You are an elite LaTeX Resume Architect and ATS Optimization Engine. Your goal is to maximize the candidate's ATS pass rating (90%–95%+) by adapting the candidate's existing resume in-place to match the target job description (JD) with concrete engineering evidence, architectural depth, and quantifiable metrics.

CANONICAL SKILLS TEMPLATES (JSON SCHEMAS BY STACK):
Use the structured JSON schema corresponding to the identified target stack as the baseline for \section{SKILLS}:

{
  "JAVA_STACK_SKILLS": {
    "Languages": ["Java (11/17/21)", "SQL", "Python", "JavaScript", "TypeScript"],
    "Backend & Frameworks": ["Spring Boot 3", "Spring MVC", "Spring Security", "Spring Data JPA", "Hibernate", "jOOQ", "FastAPI", "REST APIs", "Microservices"],
    "AI Developer Tools & GenAI": ["Claude Code", "Cursor", "GitHub Copilot", "LLMs", "RAG", "LangGraph", "LangChain", "Multi-Agent Systems", "Model Context Protocol (MCP)", "Prompt Engineering"],
    "Messaging & Distributed Systems": ["RabbitMQ", "Redis", "CompletableFuture", "Asynchronous Processing", "Event-Driven Architecture"],
    "Databases & Cloud": ["PostgreSQL", "MongoDB", "SQL Server", "AWS (EC2, S3, RDS, Cognito)", "GCP", "Azure", "Cloudflare R2", "Docker", "Kubernetes", "Linux", "GitHub Actions", "CI/CD"],
    "Testing, Frontend & Practices": ["JUnit 5", "Mockito", "Pytest", "Postman", "React 18", "HTML5", "CSS3", "Agile/Scrum", "Code Review", "System Design", "Git"]
  },
  "DOTNET_STACK_SKILLS": {
    "Languages & Core": ["C#", ".NET 6/8", "ASP.NET Core", "Entity Framework Core", "LINQ", "SQL", "Python", "TypeScript", "JavaScript"],
    "Backend & APIs": ["RESTful APIs", "Web API", "Microservices", "Swagger/OpenAPI", "async/await", "Task Parallel Library (TPL)", "FastAPI", "RabbitMQ", "Redis Caching", "OAuth2", "JWT"],
    "AI Developer Tools & GenAI": ["Claude Code", "Cursor", "GitHub Copilot", "LLMs", "RAG", "LangGraph", "LangChain", "Multi-Agent Systems", "Model Context Protocol (MCP)", "Prompt Engineering"],
    "Databases & Cloud": ["SQL Server (T-SQL, stored procedures)", "PostgreSQL", "MongoDB", "Azure (App Services, Blob Storage)", "AWS (EC2, S3, RDS, Cognito)", "GCP", "Cloudflare R2", "Docker", "Linux", "Azure DevOps", "GitHub Actions", "CI/CD"],
    "Testing, Frontend & Practices": ["xUnit", "Moq", "Pytest", "Postman", "React 18", "HTML5", "CSS3", "SOLID", "structured logging", "Agile/Scrum", "Code Review", "System Design", "Git"]
  },
  "PYTHON_STACK_SKILLS": {
    "Languages": ["Python (3.10+)", "SQL", "Java", "TypeScript", "JavaScript", "Bash"],
    "Backend & APIs": ["FastAPI", "Flask", "Django", "Pydantic", "AsyncIO", "SQLAlchemy", "REST APIs", "WebSockets", "Microservices", "Spring Boot"],
    "AI Developer Tools & GenAI": ["Claude Code", "Cursor", "GitHub Copilot", "LLMs", "RAG", "Embeddings", "LangGraph", "LangChain", "Multi-Agent Systems", "Model Context Protocol (MCP)", "Prompt Engineering"],
    "Messaging & Distributed Systems": ["RabbitMQ", "Redis", "Asynchronous Processing", "Background Tasks", "Event-Driven Architecture"],
    "Databases & Cloud": ["PostgreSQL", "MongoDB", "SQL Server", "Supabase", "AWS (EC2, S3, RDS, Cognito)", "GCP", "Azure", "Cloudflare R2", "Docker", "Kubernetes", "Linux", "GitHub Actions", "CI/CD"],
    "Testing, Frontend & Practices": ["pytest", "unittest", "JUnit 5", "Postman", "React", "Next.js", "HTML5", "CSS3", "Agile/Scrum", "Code Review", "System Design", "Git"]
  },
  "NODE_STACK_SKILLS": {
    "Languages": ["TypeScript", "JavaScript (Node.js)", "Python", "SQL", "Java"],
    "Backend & Tooling": ["Node.js", "Express.js", "NestJS", "FastAPI", "REST APIs", "WebSockets", "Microservices", "Event-Driven Architecture", "CLI Tooling", "Pydantic", "Prisma ORM"],
    "Frontend": ["React 18", "Next.js", "TypeScript", "HTML5", "CSS3"],
    "GenAI & Agents": ["Claude Code", "AWS Bedrock", "CrewAI", "LangGraph", "LangChain", "Model Context Protocol (MCP)", "Tool Calling", "Agentic RAG", "Human-in-the-Loop", "Prompt Engineering"],
    "LLMOps": ["LangSmith (Tracing, Evals, Datasets)", "RAGAS", "LLM-as-Judge", "Guardrails", "Cost and Latency Tracking"],
    "Cloud & Data": ["AWS (Bedrock, Lambda, EC2, S3, RDS, Cognito, CloudWatch, API Gateway)", "GCP", "Azure", "Docker", "Kubernetes", "GitHub Actions", "CI/CD", "Redis", "RabbitMQ", "PostgreSQL (pgvector)", "Supabase", "MongoDB", "SQL Server", "Linux"],
    "Testing & Practices": ["Jest", "Supertest", "pytest", "JUnit 5", "Mockito", "OAuth2 (PKCE)", "JWT", "RBAC", "Agile/Scrum", "Code Review", "Git"]
  },
  "AI_STACK_SKILLS": {
    "Languages": ["Python", "SQL", "TypeScript", "JavaScript", "Java"],
    "GenAI & Agents": ["LangChain", "LangGraph", "Multi-Agent Systems", "Tool Calling", "Model Context Protocol (MCP)", "Agentic RAG", "Corrective RAG", "Prompt Engineering", "OpenAI / Anthropic / Gemini APIs", "Hugging Face"],
    "LLMOps & Evaluation": ["LangSmith (Tracing, Evals, Datasets)", "RAGAS", "LLM-as-Judge", "Guardrails", "Hallucination & Citation Evals", "Cost and Latency Tracking"],
    "Backend": ["FastAPI", "AsyncIO", "Pydantic", "SQLAlchemy", "Django", "Flask", "REST APIs", "WebSockets", "Microservices", "Spring Boot"],
    "Retrieval & Data": ["PostgreSQL (pgvector)", "Supabase", "Qdrant", "Pinecone", "MongoDB", "SQL Server", "Embeddings", "Hybrid Search (BM25 + Dense, RRF)", "Reranking", "HNSW"],
    "Cloud & DevOps": ["AWS (EC2, S3, RDS, Lambda, Cognito, CloudWatch)", "GCP (Vertex AI, Cloud Run)", "Azure", "Docker", "Kubernetes", "GitHub Actions", "CI/CD", "Redis", "RabbitMQ", "Linux"],
    "Practices & Testing": ["Agile/Scrum", "Code Review", "System Design", "Git", "OAuth2 (PKCE)", "JWT", "pytest", "JUnit 5"]
  }
}

MANDATORY OPERATIONAL RULES:
1. OUTPUT: Return pure compilable LaTeX starting from \documentclass to \end{document}. No markdown fences (no ```latex), no conversational text.
2. EXACT BULLET BUDGET INTEGRITY:
   - You MUST preserve the exact bullet count per section and item as present in the source LaTeX. Do NOT add new bullets, delete existing bullets, or split bullet items. Reword phrasing in-place to highlight target JD keywords, frameworks, and architectural patterns.
3. CANONICAL ARCHETYPE STRUCTURE & SECTION ORDER:
   - For AI / ML roles: \section{PROJECTS} MUST strictly precede \section{EXPERIENCE} (the agentic projects are the primary evidence).
   - For Java, .NET, Python, and Node.js roles: \section{EXPERIENCE} MUST strictly precede \section{PROJECTS}.
   - Maintain exact reverse-chronological order in Experience:
     1. University of South Florida (Jan 2025 -- May 2026)
     2. Cognizant Technology Solutions (Feb 2022 -- Aug 2024)
   - Strictly preserve the candidate's exact set of projects and experiences from the provided source LaTeX. Do NOT drop, replace, or invent projects or employers.
   - Preserve the header exactly: the bold role-title line under the name (adjust its wording to the target role title only), the contact line with the printed URLs (linkedin.com/in/tarunmannava, github.com/tarunmannava), and the printed project URL (skillbeacon-six.vercel.app). Never replace a printed URL with the word "Link".
3b. BULLET STYLE (MECHANISM + STRUCTURAL OUTCOME) -- apply to every bullet you touch:
   - Pattern: strong past-tense verb + the specific mechanism (what was changed and with which tool) + an outcome that follows from the structure of the change.
   - Quantify from structure or scope, never from memory or invention. Good: "collapsing dozens of queries per request into single-digit round trips", "so end-to-end validation time tracked the slowest validator instead of the sum", "moving the bulk of read traffic off SQL Server", "across 8+ microservices", "13 modules serving 60+ users". Bad: "improved latency by 30%", "reduced costs 40%", "increased efficiency".
   - NEVER introduce a round percentage or multiplier gain (e.g. 30%, 40%, 2x, 10x) that is not already present in the source LaTeX. The only percentages allowed are the ones already in the source (e.g. 70\% coverage, 90\%+ pass rate).
   - Do not end a bullet with a vague result clause such as "improving performance", "reducing regressions", or "enhancing user experience" -- either state the structural outcome or stop after the mechanism.
   - Keep each bullet to at most two rendered lines (roughly 30 words). Put the strongest number available in the FIRST bullet of each employer.
   - Name the domain in the first Cognizant bullet ("healthcare insurance platform") and keep "20K+ peak hourly requests" there.
4. ZERO CROSS-SECTION PHRASING DUPLICATION:
   - DO NOT repeat identical toolchains or responsibilities across multiple sections.
   - SkillBeacon must focus on full-stack architecture, Skill Passport verification, automated job matching & LaTeX document compilation, Google OAuth2 / Gmail API digest background daemon, and Cloudflare R2 storage.
   - AutoDocs must focus on GitHub Webhooks, RabbitMQ job decoupling, MCP AST servers, and LangGraph multi-agent dynamic task routing.
5. METRIC PRESERVATION (NO HALLUCINATED METRICS):
   - Preserve real scale metrics from the base resume: '20K+ peak hourly requests' (belongs EXCLUSIVELY to Cognizant), 'under 2 seconds' interactive latency (USF), '70\%' backend coverage (Cognizant), '60+ biomedical students and faculty' across '13 interactive modules' (USF), '8+ microservices' (Cognizant), '90\%+ pass rate' (AutoDocs), '50-query' and '20-ticker' golden sets (ProofStack, FinScope).
   - NEVER copy '20K+' into USF or projects.
   - Do NOT invent arbitrary new percentage gains or random multipliers (see rule 3b).
6. STACK-SPECIFIC EXPERIENCE & SKILLS RULES:
   - For .NET roles: USF is Behavioral Health platform in C#, .NET 8, ASP.NET Core Web API, Swagger/OpenAPI, and EF Core. Cognizant is C#, ASP.NET Core (.NET 6/8), EF Core, LINQ, SQL Server stored procedures, IDistributedCache Redis, async/await + Task.WhenAll, Swagger/OpenAPI, SOLID, structured logging/metrics, Azure DevOps pipelines, and xUnit/Moq (never NUnit; never ".NET 8" alone for Cognizant -- write ".NET 6/8"). Strictly maintain reverse-chronological order: 1. USF (Jan 2025 -- May 2026), 2. Cognizant (Feb 2022 -- Aug 2024). Use DOTNET_STACK_SKILLS (strictly purge Java/Spring from SKILLS, but PRESERVE FastAPI, RabbitMQ, MCP, Multi-Agent, and Cloudflare R2 in projects).
   - For Java roles: USF is Behavioral Health platform in Java 17, Spring Boot, jOOQ, React 18, and JUnit 5/Mockito. Cognizant is Java 11, Spring Boot enterprise microservices with MongoDB/SQL Server, Spring Data JPA/Hibernate, CompletableFuture/ExecutorService, multi-tier Redis, Spring Security OAuth2 + AWS Cognito, JUnit 5/Mockito (strictly maintain reverse-chronological order: 1. USF [Jan 2025 -- May 2026], 2. Cognizant [Feb 2022 -- Aug 2024]). Use JAVA_STACK_SKILLS.
   - For Node.js roles: USF features React 18, TypeScript, and Node.js backend microservices with Express and Prisma ORM, real-time AWS Bedrock/Hugging Face dual-model sandbox, the MyFoodRx RAG chatbot, and Jest/Supertest. Cognizant is Java 11 / Spring Boot enterprise foundation. Projects feature SkillBeacon, AutoDocs, ProofStack, and JobPilot. Use NODE_STACK_SKILLS.
   - For AI / ML roles: USF features the AI & Health Literacy platform with Python/FastAPI backend, the MyFoodRx RAG chatbot (multi-layer safety, cosine-similarity retrieval, rate-limit-aware Redis caching over Gemini), Groq/HF dual-model sandbox, Transformers.js WASM prompt evaluation. Projects feature ProofStack, AutoDocs, FinScope, and JobPilot. Cognizant is Java 11 / Spring Boot. Use AI_STACK_SKILLS.
   - For Python roles: USF features Python, FastAPI, AsyncIO, SQLAlchemy, and the MyFoodRx RAG chatbot. Cognizant is Java 11 / Spring Boot. Projects feature SkillBeacon and AutoDocs. Use PYTHON_STACK_SKILLS.
   - USF title is "Graduate Research Assistant, Software Engineer" in every stack. Location is "Seattle, WA" unless a target location override is provided.
   - STRICTLY BANNED FROM COGNIZANT: Do NOT mention GitHub Actions, RabbitMQ, Cloudflare R2, or payment gateways in Cognizant. Azure DevOps build and release pipelines ARE allowed at Cognizant; do not write the phrase "CI/CD" there (the sanitizer strips it). GitHub Actions belongs in USF/Projects only.
7. IMMUTABLE PROJECT TECH STACKS (AUTHENTICITY):
   - Keep project tech stacks authentic as indicated in the source LaTeX. Do NOT rewrite SkillBeacon or AutoDocs into .NET or Java.
8. CLEAN BULLETS (ZERO INLINE BOLDING):
   - All text inside \resumeItem{...} MUST be 100% clean plain text. ZERO \textbf{...} tags inside bullet items.
9. SYNTAX & LOCATION INTEGRITY:
   - Escape all percentages as \% (e.g. 70\%) and ampersands as \& (e.g. Cloud \& DevOps).
   - Always preserve the CERTIFICATIONS section exactly as in the source: AWS Certified AI Practitioner (AIF-C01), AWS Certified Cloud Practitioner (Nov 2023), Microsoft Certified: Azure Fundamentals (AZ-900). Never add, drop, or rename a certification. GCP appears only in SKILLS, never as a certification.
   - Preserve the candidate's location in \resumeHeadingContact unless a specific target location override is provided.
10. PROFESSIONAL SUMMARY:
   - Must prominently begin with the candidate's years of experience: "[Role Title] with 3+ years of experience..." (or 4+ years for AI/Node).
   - The Professional Summary MUST be placed as an italicized block (\textit{...}) directly inside \begin{center}...\end{center} immediately below \resumeHeadingContact \\[4pt]. Do NOT create a separate \section{SUMMARY} heading; always maintain it within the centered candidate header.
   - For .NET roles: "Full Stack Software Engineer with 3+ years of experience specializing in C\#, .NET 6/8 and ASP.NET Core, and distributed systems alongside modern React frontends. Experienced in enterprise Web APIs (Swagger/OpenAPI), Entity Framework Core and SQL Server optimization, Azure DevOps pipelines, Azure and AWS cloud services, structured logging and metrics, and building AI-in-the-loop solutions with custom AI skills and automated evaluation pipelines."
   - For Java roles: "Full Stack Software Engineer with 3+ years of experience building high-throughput microservices in Java 11/17 and Spring Boot alongside responsive React/TypeScript frontends. Proven track record in relational and NoSQL database optimization (PostgreSQL, MongoDB, SQL Server), event-driven messaging with RabbitMQ, and building AI-assisted solutions with AI-in-the-loop validation and custom AI skills."
   - For Python roles: "Full Stack Software Developer with 3+ years of experience building asynchronous backend microservices in Python 3.10+, FastAPI, and React frontends. Proven expertise in relational and NoSQL data modeling (SQLAlchemy, PostgreSQL, MongoDB), background task pipelines with RabbitMQ and Redis, and building production AI solutions with AI-in-the-loop workflows."
   - For Node.js / Fullstack roles: "AI & Software Engineer with 4+ years of experience building scalable backend services and production agentic AI systems across Node.js, Python, and AWS. Specializing in multi-agent orchestration (Claude Code, LangGraph, CrewAI, AWS Bedrock), Model Context Protocol (MCP) server development, and developer productivity tooling, with hands-on experience in custom agent harnesses, enterprise API integrations, human-in-the-loop workflows, and LLM observability with LangSmith and CloudWatch."
   - For AI / ML roles: "AI & Software Engineer with 4+ years of experience building production LLM systems and scalable backend services. Specializing in LangGraph multi-agent orchestration, Model Context Protocol (MCP) tool integration, agentic and corrective RAG, and LangSmith evaluation pipelines, on a foundation of high-throughput Java and Python microservices, PostgreSQL, Redis caching, and AWS."
   - You MAY weave 2-4 exact JD keywords into the summary, but keep the years-of-experience opener and the sentence structure above.
"""

SYSTEM_PROMPT_TITLE_ALIGNMENT = """
TITLE ALIGNMENT MODE IS ENABLED. Additional rules:
- You MAY adjust the candidate's job titles in the LaTeX to better align with the target role name provided, but ONLY within these strict boundaries:
  1. The new title must be a genuine synonym or a level-appropriate variant of the original title (e.g. "Software Developer" -> "Software Engineer", "Jr. Developer" -> "Junior Software Engineer", "Backend Developer" -> "Backend Engineer").
  2. Do NOT change a title to a completely different discipline (e.g. do NOT change "Frontend Developer" to "DevOps Engineer" or "Data Scientist").
  3. Do NOT inflate seniority beyond what is defensible (e.g. do NOT change "Junior Developer" to "Senior Engineer" or "Lead").
  4. Do NOT invent titles that were never held.
  5. If the original title is already a close match to the target role, leave it unchanged.
"""


def build_system_prompt(align_titles: bool) -> str:
    if align_titles:
        return SYSTEM_PROMPT_BASE.rstrip() + "\n" + SYSTEM_PROMPT_TITLE_ALIGNMENT
    return SYSTEM_PROMPT_BASE


def build_user_prompt(
    request: RewriteRequest,
    missing_terms: list[str],
    unsupported_terms: list[str],
    target_stack: str,
    industry: str,
) -> str:
    confirmed = ", ".join(request.confirmed_skills) or "None provided"
    banned = ", ".join(request.banned_skills) or "None provided"
    company_context = request.company_context or "None provided"
    notes = request.extra_user_notes or "None provided"
    target_role = request.role_name or "Not specified"
    target_location = request.target_location or "Not specified (preserve existing)"

    # Determine stack instructions based on target_stack matrix
    if target_stack == "dotnet":
        usf_instruction = (
            "USF EXPERIENCE (.NET / C#): Prototyped Behavioral Health Workflow Platform in C#, .NET 8, ASP.NET Core Web API, EF Core, LINQ, and React 18 / TypeScript Recharts dashboards with xUnit and Moq testing."
        )
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (.NET / C#): Adapt Cognizant Technology Solutions to C#, ASP.NET Core (.NET 6/8), "
            "Entity Framework Core + LINQ, IDistributedCache Redis, SQL Server, MongoDB, async/await + Task.WhenAll, and xUnit/Moq testing (never NUnit). "
            "SKILLS PURGE: Remove all Java-specific frameworks from SKILLS and replace them with DOTNET_STACK_SKILLS."
        )
        projects_instruction = (
            "PROJECTS (.NET): Preserve authentic projects (SkillBeacon & AutoDocs). "
            "DO NOT rewrite project technology stacks into .NET/C#."
        )
        order_instruction = "SECTION ORDER: \\section{EXPERIENCE} MUST precede \\section{PROJECTS}."
    elif target_stack == "java":
        usf_instruction = (
            "USF & PROJECTS RULE (JAVA): Adapt USF Graduate Researcher to Java 17, Spring Boot, jOOQ, "
            "PostgreSQL, Apache POI, and React 18 / TypeScript Recharts dashboards with JUnit 5 and Mockito testing."
        )
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (JAVA TARGET STACK): Cognizant MUST be Java 11 / Spring Boot, "
            "Microservices, REST APIs, SQL Server/MongoDB persistence, Spring Data JPA/Hibernate query tuning, CompletableFuture concurrency, "
            "multi-tier Redis caching, AWS Cognito IAM, and JUnit 5/Mockito testing."
        )
        projects_instruction = (
            "PROJECTS (JAVA): Preserve authentic projects (SkillBeacon & AutoDocs)."
        )
        order_instruction = "SECTION ORDER: \\section{EXPERIENCE} MUST precede \\section{PROJECTS}."
    elif target_stack == "node":
        usf_instruction = (
            "USF EXPERIENCE (NODE.JS): Production AI & Health Literacy web platform across 13 modules in React, TypeScript, and Node.js backend microservices with Express and Prisma ORM, AWS Bedrock and Hugging Face dual-model sandbox, MyFoodRx RAG chatbot, Transformers.js WASM, and Jest/Supertest."
        )
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (NODE.JS): Cognizant Technology Solutions MUST remain Java / Spring Boot enterprise foundation."
        )
        projects_instruction = (
            "PROJECTS (NODE.JS): All 4 projects MUST be preserved: SkillBeacon, AutoDocs, ProofStack, JobPilot (highlighting Node.js, TypeScript, Next.js, and agentic workflows)."
        )
        order_instruction = "SECTION ORDER: \\section{EXPERIENCE} MUST precede \\section{PROJECTS}."
    elif target_stack == "ai":
        usf_instruction = (
            "USF EXPERIENCE (AI / GENAI): Production AI & Health Literacy platform in React/TypeScript with Python/FastAPI backend, MyFoodRx RAG chatbot with multi-layer safety, Groq & HF dual-model sandbox, Transformers.js WASM evaluation."
        )
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (AI): Cognizant Technology Solutions MUST remain Java / Spring Boot enterprise foundation."
        )
        projects_instruction = (
            "PROJECTS (AI): 4 agentic/MCP projects MUST be preserved: ProofStack, AutoDocs, FinScope, and JobPilot (highlighting LangGraph, MCP, LangSmith, and corrective RAG)."
        )
        order_instruction = "SECTION ORDER: \\section{PROJECTS} MUST strictly precede \\section{EXPERIENCE}."
    else:  # python
        usf_instruction = (
            "USF EXPERIENCE (PYTHON): Python 3.10+, FastAPI, AsyncIO, SQLAlchemy, real-time dual-model sandbox Groq/HF, in-browser Transformers.js WASM evaluation, and MyFoodRx RAG chatbot."
        )
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (PYTHON): Cognizant Technology Solutions MUST remain Java / Spring Boot enterprise foundation."
        )
        projects_instruction = (
            "PROJECTS (PYTHON): SkillBeacon and AutoDocs (featuring Python, FastAPI, AsyncIO, RabbitMQ, and MCP)."
        )
        order_instruction = "SECTION ORDER: \\section{EXPERIENCE} MUST precede \\section{PROJECTS}."

    missing_str = ", ".join(missing_terms) if missing_terms else "None (strong initial keyword match)"

    prompt = f"""TARGET JOB DESCRIPTION:
{request.job_description}

TARGET ROLE NAME: {target_role}
TARGET LOCATION (CITY, STATE): {target_location}
TARGET INDUSTRY CONTEXT: {industry}
DETECTED PRIMARY STACK: {target_stack.upper()} (Use {target_stack.upper()}_STACK_SKILLS schema for SKILLS)
IDENTIFIED ATS CRITERIA & KEYWORD GAPS TO RESOLVE: {missing_str}
COMPANY CONTEXT: {company_context}
USER CONFIRMED SKILLS: {confirmed}
BANNED SKILLS (DO NOT INCLUDE): {banned}
EXTRA USER NOTES: {notes}

CRITICAL STACK & ROLE INSTRUCTIONS:
- {order_instruction}
- {usf_instruction}
- {cognizant_instruction}
- {projects_instruction}
- STRICT REVERSE-CHRONOLOGICAL ORDER: The Experience section MUST strictly be ordered: 1. University of South Florida (Jan 2025 -- May 2026), 2. Cognizant Technology Solutions (Feb 2022 -- Aug 2024).
- STRICT BULLET BUDGET: Preserve the exact bullet count per section and item as present in the source LaTeX. Do NOT add, delete, or split bullets.
- ZERO CROSS-SECTION DUPLICATION: Do NOT repeat CI/CD or Docker lines across multiple sections. SkillBeacon focuses on platform & R2; AutoDocs focuses on Webhooks, RabbitMQ, and MCP multi-agent routing.
- METRIC PRESERVATION: '20K+ peak hourly requests' belongs EXCLUSIVELY to Cognizant. Do NOT clone '20K+' into USF or AutoDocs. Do NOT invent new percentage numbers.
- BULLET STYLE: verb + specific mechanism + structural outcome (see system rule 3b). Quantify from structure or scope ("collapsing dozens of queries per request into single-digit round trips", "so validation time tracked the slowest validator instead of the sum"), never with an invented percentage or multiplier. No vague trailing clauses like "improving performance".
- HEADER TITLE: The bold role-title line under the candidate's name MUST always be a clean, standard professional engineering title (e.g. \\textbf{{Software Engineer}}, \\textbf{{Software Developer}}, \\textbf{{Full Stack Software Engineer}}, or \\textbf{{AI Engineer}}). NEVER copy raw job posting titles, company-specific team names, language tags, or weird JD suffixes (e.g. NEVER output "\\textbf{{Software Engineer - Ruby}}", "\\textbf{{Manufacturing Systems}}", or specialized employer qualifiers). Keep it strictly standard and professional. Keep printed URLs (linkedin.com/in/tarunmannava, github.com/tarunmannava, skillbeacon-six.vercel.app), and keep the CERTIFICATIONS block verbatim.
- Clean bullets: Pure plain text with ZERO \\textbf{{...}} inside \\resumeItem{{...}}.
- Cognizant Scope: Do NOT claim GitHub Actions, RabbitMQ, or Cloudflare in Cognizant. Azure DevOps pipelines are allowed; do not use the phrase CI/CD in Cognizant bullets.
{"- Location: Begin \\resumeHeadingContact with '" + target_location + "'." if target_location and target_location != "Not specified (preserve existing)" else ""}

SOURCE LATEX RESUME TO REWRITE:
{request.resume_latex}

Please output the complete, rewritten LaTeX document below from \\documentclass to \\end{{document}} without markdown fences.
"""
    return prompt


def generate_with_openai(prompt: str, align_titles: bool = False) -> tuple[str | None, str | None]:
    settings = get_settings()
    if not settings.openai_api_key:
        return None, "OpenAI API key not configured"
    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    is_preset = bool(settings.openai_model and settings.openai_model.startswith("@"))
    
    messages = []
    if not is_preset:
        messages.append({"role": "system", "content": build_system_prompt(align_titles)})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": settings.openai_model,
        "messages": messages,
    }
    if not is_preset:
        kwargs["temperature"] = 0.3
        kwargs["top_p"] = 0.95
        kwargs["max_tokens"] = settings.max_output_tokens

    if not is_preset and settings.openai_base_url and "nvidia.com" in settings.openai_base_url:
        kwargs["extra_body"] = {
            "chat_template_kwargs": {
                "thinking": True,
                "reasoning_effort": "high",
            }
        }
    elif not is_preset and settings.openai_base_url and "openrouter.ai" in settings.openai_base_url:
        kwargs["extra_headers"] = {"X-OpenRouter-Cache": "false"}
        kwargs["extra_body"] = {
            "reasoning": {
                "effort": "medium"
            }
        }
    try:
        completion = client.chat.completions.create(**kwargs)
        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content, None
        return None, "OpenAI returned empty completion choices"
    except Exception as exc:
        logger.error("OpenAI/OpenRouter call failed: %s", exc)
        return None, f"OpenAI error: {exc}"


def generate_with_gemini(prompt: str, align_titles: bool = False) -> tuple[str | None, str | None]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None, "Gemini API key not configured"
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(align_titles),
            temperature=0.25,
            max_output_tokens=settings.max_output_tokens,
        ),
    )
    if response.candidates and len(response.candidates) > 0:
        return response.text, None
    return None, "Gemini returned empty response"


def generate_rewrite(prompt: str, align_titles: bool = False) -> tuple[str | None, str, str | None]:
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()
    if provider == "gemini":
        text, err = generate_with_gemini(prompt, align_titles)
        return text, "gemini", err
    if provider == "openai":
        text, err = generate_with_openai(prompt, align_titles)
        return text, "openai", err
    return None, provider, f"Unsupported AI provider '{provider}'"


def repair_truncated_latex(latex: str) -> str:
    """Repairs truncated LaTeX code by balancing braces, closing custom lists, and ending open environments."""
    # If it already ends with \end{document} AND has substantial, meaningful body content, no repair needed
    if latex.strip().endswith(r"\end{document}"):
        if r"\begin{document}" in latex:
            body_start = latex.find(r"\begin{document}") + len(r"\begin{document}")
            body_end = latex.rfind(r"\end{document}")
            body_content = latex[body_start:body_end].strip()
            has_semantic_content = (
                len(body_content) > 100
                and any(marker in body_content for marker in (
                    "\\section", "\\resumeItem", "\\resumeSubheading",
                    "\\resumeProject", "\\resumeSubHeadingListStart",
                ))
            )
            if has_semantic_content:
                return latex
        else:
            return latex

    # Remove any trailing incomplete backslash commands or partial macros at the very end
    latex = re.sub(r"\\[a-zA-Z]*$", "", latex)

    # Balance braces (ignoring escaped ones \{ and \})
    clean_text = re.sub(r"\\\{", "", latex)
    clean_text = re.sub(r"\\\}", "", clean_text)
    
    open_braces = clean_text.count("{")
    close_braces = clean_text.count("}")
    if open_braces > close_braces:
        latex += "}" * (open_braces - close_braces)

    # Close custom lists if they are open
    item_list_starts = latex.count(r"\resumeItemListStart")
    item_list_ends = latex.count(r"\resumeItemListEnd")
    if item_list_starts > item_list_ends:
        latex += "\n" + (r"\resumeItemListEnd" * (item_list_starts - item_list_ends))

    sub_list_starts = latex.count(r"\resumeSubHeadingListStart")
    sub_list_ends = latex.count(r"\resumeSubHeadingListEnd")
    if sub_list_starts > sub_list_ends:
        latex += "\n" + (r"\resumeSubHeadingListEnd" * (sub_list_starts - sub_list_ends))

    # Balance standard LaTeX environments
    stack = []
    tokens = re.finditer(r"\\(begin|end)\{([^}]+)\}", latex)
    for match in tokens:
        cmd, env = match.groups()
        if cmd == "begin":
            stack.append(env)
        elif cmd == "end":
            if stack and stack[-1] == env:
                stack.pop()

    for env in reversed(stack):
        latex += f"\n\\end{{{env}}}"

    # Ensure it ends with \end{document} if \begin{document} was present
    if r"\begin{document}" in latex and r"\end{document}" not in latex:
        latex += "\n\\end{document}"

    return latex


def remove_inline_bolding_from_bullets(latex_str: str) -> str:
    """
    Strips \\textbf{} markup from within resume bullet items (\\resumeItem{...})
    while preserving \\textbf{} in section headers, company names, and skill categories.
    """
    def unwrap_bullet(match: re.Match) -> str:
        content = match.group(1)
        while "\\textbf{" in content:
            content = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", content)
        return f"\\resumeItem{{{content}}}"

    return re.sub(r"\\resumeItem\{((?:[^{}]|\{[^{}]*\})*)\}", unwrap_bullet, latex_str)


def enforce_reverse_chronological_experience(latex: str) -> str:
    """Ensure Experience entries strictly follow reverse-chronological sequence across all roles:
    1. University of South Florida (Jan 2025 -- May 2026)
    2. Cognizant Technology Solutions (Feb 2022 -- Aug 2024)
    """
    exp_match = re.search(
        r"(\\section\{(?:EXPERIENCE|Work Experience)\}\s*(?:%[^\n]*\n\s*)*(?:\\resumeSubHeadingListStart|\\begin\{itemize\}|\\begin\{enumerate\})\s*)(.*?)(\s*(?:\\resumeSubHeadingListEnd|\\end\{itemize\}|\\end\{enumerate\}))",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not exp_match:
        return latex

    header, body, footer = exp_match.groups()
    entries = [e for e in re.split(r"(?=\\resumeSubheading)", body) if e.strip()]
    usf_entry = [e for e in entries if "University of South Florida" in e or "South Florida" in e]
    cog_entry = [e for e in entries if "Cognizant" in e]
    other_entries = [e for e in entries if e not in usf_entry and e not in cog_entry]

    reordered_entries = usf_entry + cog_entry + other_entries
    if reordered_entries:
        reordered_body = "\n\n  ".join(e.strip() for e in reordered_entries).strip()
        return latex[: exp_match.start(0)] + header + "\n  " + reordered_body + "\n" + footer + latex[exp_match.end(0) :]
    return latex


# Backward-compatible alias
reorder_experience_for_java = enforce_reverse_chronological_experience


def update_contact_location(latex_str: str, target_location: str | None) -> str:
    """
    Updates the city, state in \\resumeHeadingContact if target_location is provided.
    """
    if not target_location or not target_location.strip():
        return latex_str
    
    loc = target_location.strip()
    # Match \newcommand{\resumeHeadingContact}{City, ST ... or {Seattle, WA ...
    pattern = r"(\\newcommand\{\\resumeHeadingContact\}\{)[^\\}]+?(\s*\\hspace\{0\.4em\}\\resumeSep)"
    if re.search(pattern, latex_str):
        return re.sub(pattern, rf"\g<1>{loc}\g<2>", latex_str, count=1)
    
    # Alternatively in \begin{center} ... City, ST ...
    alt_pattern = r"((\\begin\{center\}\s*\{\\Huge\s*\\textbf\{[^}]+\}\}\s*\\\\(?:\[\d+pt\])?\s*\\small\s*)(?:[A-Za-z\s]+,\s*[A-Z]{2}))"
    if re.search(alt_pattern, latex_str):
        return re.sub(alt_pattern, rf"\g<2>{loc}", latex_str, count=1)
    
    return latex_str


def preserve_certifications_section(original_latex: str, rewritten_latex: str) -> str:
    """Ensures the candidate's original certifications are preserved and never lost or emitted empty."""
    orig_match = re.search(
        r"(\\section\{(?:CERTIFICATIONS|CERTIFICATION)\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        original_latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not orig_match:
        # Original has no certifications; strip any empty or hallucinated certifications block from rewritten
        return re.sub(
            r"\\section\{(?:CERTIFICATIONS|CERTIFICATION)\}\s*(?:\\begin\{[^{}]*\}\[[^\]]*\]|\\begin\{[^{}]*\}|\s|%[^\n]*)*(?:\\end\{[^{}]*\}|\Z|(?=\\section\{))",
            "",
            rewritten_latex,
            flags=re.IGNORECASE,
        )

    orig_cert_block = orig_match.group(1).strip()

    # Check if rewritten has certifications
    rewritten_match = re.search(
        r"(\\section\{(?:CERTIFICATIONS|CERTIFICATION)\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        rewritten_latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if rewritten_match:
        # Check if rewritten block is missing items or has no content
        rewritten_block = rewritten_match.group(1)
        cleaned_content = re.sub(r"\\(?:section|begin|end|small|large|Huge|item)\b(\[[^\]]*\])?(\{.*?\})?", "", rewritten_block)
        cleaned_content = re.sub(r"[{}\s%]", "", cleaned_content)
        if len(cleaned_content) < 5:  # empty or missing certification text
            # Replace with original certification block
            rewritten_latex = (
                rewritten_latex[: rewritten_match.start(1)]
                + orig_cert_block
                + "\n\n"
                + rewritten_latex[rewritten_match.end(1) :]
            )
    else:
        # Rewritten completely omitted certifications; insert before \end{document}
        end_doc_idx = rewritten_latex.find(r"\end{document}")
        if end_doc_idx != -1:
            rewritten_latex = (
                rewritten_latex[:end_doc_idx].rstrip()
                + "\n\n"
                + orig_cert_block
                + "\n\n"
                + rewritten_latex[end_doc_idx:]
            )
    return rewritten_latex


def clean_cognizant_guardrails(latex: str) -> str:
    """Removes any accidental mentions of GitHub Actions, CI/CD, RabbitMQ, or Cloudflare from Cognizant."""
    cog_match = re.search(
        r"(\\resumeSubheading\s*\{[^}]*Cognizant.*?)(\s*\\resumeSubheading|\s*\\resumeSubHeadingListEnd|\s*\\end\{itemize\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if cog_match:
        cog_block = cog_match.group(1)
        cleaned_cog = re.sub(
            r"\\resumeItem\{[^}]*(?:GitHub Actions|CI/CD|RabbitMQ|Cloudflare)[^}]*\}\s*",
            "",
            cog_block,
            flags=re.IGNORECASE,
        )
        if cleaned_cog != cog_block:
            latex = latex[: cog_match.start(1)] + cleaned_cog + latex[cog_match.start(2) :]
    return latex


DOTNET_COGNIZANT_BLOCK = r"""  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed C\# and ASP.NET Core (.NET 6/8) microservices for policy onboarding and validation on a healthcare insurance platform, exposing Swagger/OpenAPI-documented REST APIs and persisting client metadata in MongoDB and relational records in SQL Server at 20K+ peak hourly requests.}
    \resumeItem{Eliminated N+1 query patterns in policy audit and reporting endpoints by replacing per-row lookups with batched LINQ queries, Entity Framework Core eager loading, composite indexes, and SQL Server stored procedures, collapsing dozens of queries per request into single-digit round trips.}
    \resumeItem{Implemented multi-tier Redis distributed caching with IDistributedCache and deploy-time warm-up for policy reference data, moving the bulk of repeated read traffic off SQL Server during peak onboarding windows.}
    \resumeItem{Parallelized validation workflows with async/await and Task.WhenAll, replacing sequential downstream calls with concurrent execution so end-to-end validation time tracked the slowest validator instead of the sum.}
    \resumeItem{Refactored duplicate business logic across 8+ microservices into shared ASP.NET Core service-layer components following SOLID principles, with centralized exception-handling middleware and request validation.}
    \resumeItem{Secured REST endpoints with ASP.NET Core authentication, OAuth2, and JWT integrated with AWS Cognito, implementing role-based authorization policies.}
    \resumeItem{Raised backend coverage to 70\% with xUnit and Moq on onboarding and validation workflows. Added structured logging and application metrics, and released the services through Azure DevOps build and release pipelines.}
  \resumeItemListEnd"""

DOTNET_USF_BLOCK = r"""  \resumeSubheading
    {University of South Florida}{Graduate Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Prototyped a Behavioral Health Workflow Platform supporting session tracking, therapist workflows, and clinic resource utilization for behavioral health services.}
    \resumeItem{Engineered C\# and .NET 8 microservices to model therapist productivity, billable vs. non-billable hours, session activity, and physical room utilization across daily, weekly, and monthly reporting periods, exposing Swagger/OpenAPI-documented APIs.}
    \resumeItem{Built PostgreSQL data pipelines using Entity Framework Core and LINQ to organize session and operational data for utilization and financial analysis.}
    \resumeItem{Implemented AWS Cognito and PostgreSQL synchronization for role-based access, therapist accounts, and administrator profiles within the prototype.}
    \resumeItem{Designed session lifecycle workflows with state transitions, automated status restoration, granular session activity auditing, and Excel data exports using ClosedXML.}
    \resumeItem{Built React 18 and TypeScript dashboards with utilization metrics, Recharts trend visualizations, and custom date-range reporting.}
    \resumeItem{Developed xUnit and Moq test suites to validate backend workflows, data processing, and session state transitions.}
  \resumeItemListEnd"""

JAVA_USF_BLOCK = r"""  \resumeSubheading
    {University of South Florida}{Graduate Research Assistant, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Prototyped a Behavioral Health Workflow Platform supporting session tracking, therapist workflows, and clinic resource utilization for behavioral health services.}
    \resumeItem{Engineered Java 17 and Spring Boot microservices to model therapist productivity, billable vs. non-billable hours, session activity, and physical room utilization across daily, weekly, and monthly reporting periods.}
    \resumeItem{Built PostgreSQL data pipelines using jOOQ to organize session and operational data for utilization and financial analysis.}
    \resumeItem{Implemented AWS Cognito and PostgreSQL synchronization for role-based access, therapist accounts, and administrator profiles within the prototype.}
    \resumeItem{Designed session lifecycle workflows with state transitions, automated status restoration, granular session activity auditing, and Excel data exports using Apache POI.}
    \resumeItem{Built React 18 and TypeScript dashboards with utilization metrics, Recharts trend visualizations, and custom date-range reporting.}
    \resumeItem{Developed JUnit 5 and Mockito test suites to validate backend workflows, data processing, and session state transitions.}
  \resumeItemListEnd"""


def adapt_resume_for_dotnet(latex: str, request: RewriteRequest) -> str:
    """Strictly enforces C#/.NET 8 framing across Summary, Skills, Cognizant, and USF Experience."""
    # 1. Professional Summary guard
    center_match = re.search(r"(\\begin\{center\}.*?\\end\{center\})", latex, re.DOTALL)
    if center_match:
        center_text = center_match.group(1)
        if "Java" in center_text or "Spring" in center_text:
            dotnet_summary = (
                r"\textit{Full Stack Software Engineer with 3+ years of experience specializing in C\#, .NET 6/8 and ASP.NET Core, and distributed systems alongside modern React frontends. "
                r"Experienced in enterprise Web APIs (Swagger/OpenAPI), Entity Framework Core and SQL Server optimization, Azure DevOps pipelines, Azure and AWS cloud services, structured logging and metrics, and building AI-in-the-loop solutions with custom AI skills and automated evaluation pipelines.}"
            )
            new_center = re.sub(
                r"\\textit\{[^{}]*(?:Java|Spring)[^{}]*\}",
                lambda _m: dotnet_summary,
                center_text,
                flags=re.IGNORECASE,
            )
            if new_center == center_text:
                new_center = re.sub(r"\bJava\b", lambda _m: "C\\#", center_text)
                new_center = re.sub(r"\bSpring Boot\b", lambda _m: ".NET 8 / ASP.NET Core", center_text)
            latex = latex[: center_match.start(1)] + new_center + latex[center_match.end(1) :]

    # 2. Experience section guards (Cognizant -> .NET, USF -> .NET)
    exp_match = re.search(
        r"(\\section\{(?:EXPERIENCE|Work Experience)\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if exp_match:
        exp_block = exp_match.group(1)

        # 2a. Cognizant Experience guard
        cog_match = re.search(
            r"(\\resumeSubheading\s*\{[^}]*Cognizant.*?)(\s*\\resumeSubheading|\s*\\resumeSubHeadingListEnd|\s*\\end\{itemize\}|\Z)",
            exp_block,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if cog_match:
            cog_content = cog_match.group(1)
            if "Java" in cog_content or "Spring" in cog_content or "JUnit" in cog_content or "jOOQ" in cog_content or "CompletableFuture" in cog_content:
                exp_block = exp_block[: cog_match.start(1)] + DOTNET_COGNIZANT_BLOCK + "\n\n" + exp_block[cog_match.start(2) :]

        # 2b. USF Experience guard
        usf_match = re.search(
            r"(\\resumeSubheading\s*\{[^}]*South Florida.*?)(\s*\\resumeSubheading|\s*\\resumeSubHeadingListEnd|\s*\\end\{itemize\}|\Z)",
            exp_block,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if usf_match:
            usf_content = usf_match.group(1)
            if "Python" in usf_content or "Flask" in usf_content or "Django" in usf_content or ("C#" not in usf_content and ".NET" not in usf_content) or "Spring" in usf_content:
                exp_block = exp_block[: usf_match.start(1)] + DOTNET_USF_BLOCK + "\n\n" + exp_block[usf_match.start(2) :]

        latex = latex[: exp_match.start(1)] + exp_block + latex[exp_match.end(1) :]

    # 3. SKILLS Section: Purge Java frameworks and inject .NET technologies
    section_match = re.search(
        r"(\\section\{(?:TECHNICAL )?SKILLS\}.*?)(?=\\section\{|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if section_match:
        sec = section_match.group(1)
        if "Spring" in sec or "jOOQ" in sec or "JUnit" in sec or ("Java" in sec and "C#" not in sec):
            from .skills_data import get_skills_template_for_stack
            dotnet_tmpl = get_skills_template_for_stack("dotnet")
            if dotnet_tmpl and "raw_latex" in dotnet_tmpl:
                raw = dotnet_tmpl["raw_latex"]
                latex = latex[: section_match.start(1)] + raw + "\n\n" + latex[section_match.end(1) :]
        else:
            for term in ["Spring Boot", "Spring MVC", "Spring Security", "jOOQ", "JUnit"]:
                sec = re.sub(rf",\s*\b{re.escape(term)}\b", "", sec, flags=re.IGNORECASE)
                sec = re.sub(rf"\b{re.escape(term)}\b\s*,\s*", "", sec, flags=re.IGNORECASE)
                sec = re.sub(rf"\\;\s*\|\s*\\;\s*\b{re.escape(term)}\b", "", sec, flags=re.IGNORECASE)
                sec = re.sub(rf"\b{re.escape(term)}\b\s*\\;\s*\|\s*\\;\s*", "", sec, flags=re.IGNORECASE)
                sec = re.sub(rf"\$\|\$\s*\b{re.escape(term)}\b", "", sec, flags=re.IGNORECASE)
                sec = re.sub(rf"\b{re.escape(term)}\b\s*\$\|\$", "", sec, flags=re.IGNORECASE)
                sec = re.sub(rf"\b{re.escape(term)}\b", "", sec, flags=re.IGNORECASE)
            sec = re.sub(r"(\s*\\;\|\s*){2,}", r" \;|\; ", sec)
            sec = re.sub(r"(\s*\$\|\$\s*){2,}", " $|$ ", sec)
            sec = re.sub(r"(\s*,\s*){2,}", ", ", sec)
            latex = latex[: section_match.start(1)] + sec + latex[section_match.end(1) :]

    return latex


def adapt_resume_for_java(latex: str, request: RewriteRequest) -> str:
    """Strictly enforces Java/Spring Boot framing across Experience (Cognizant & USF)."""
    # Enforce reverse-chronological order: USF then Cognizant
    latex = enforce_reverse_chronological_experience(latex)

    # USF Experience guard (adapt USF to Java/Spring Boot Behavioral Health platform if still Python)
    exp_match = re.search(
        r"(\\section\{(?:EXPERIENCE|Work Experience)\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if exp_match:
        exp_block = exp_match.group(1)
        usf_match = re.search(
            r"(\\resumeSubheading\s*\{[^}]*South Florida.*?)(\s*\\resumeSubheading|\s*\\resumeSubHeadingListEnd|\s*\\end\{itemize\}|\Z)",
            exp_block,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if usf_match:
            usf_content = usf_match.group(1)
            if "Python" in usf_content or "Flask" in usf_content or ("Java" not in usf_content and "Spring" not in usf_content):
                exp_block = exp_block[: usf_match.start(1)] + JAVA_USF_BLOCK + "\n\n" + exp_block[usf_match.start(2) :]
                latex = latex[: exp_match.start(1)] + exp_block + latex[exp_match.end(1) :]

    return latex


def adapt_resume_for_node(latex: str, request: RewriteRequest) -> str:
    """Ensures Node.js/TypeScript skills and summary are properly reflected for Node/Fullstack roles."""
    section_match = re.search(
        r"(\\section\{(?:TECHNICAL )?SKILLS\}.*?)(?=\\section\{|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if section_match:
        sec = section_match.group(1)
        if "Node.js" not in sec and "Node" not in sec:
            from .latex_skills import inject_canonical_skills_section
            latex = inject_canonical_skills_section(latex, "node")
    return latex


def get_archetype_latex(stack: str) -> str:
    """Loads the canonical base LaTeX archetype for the requested stack."""
    stack_clean = (stack or "ai").lower().strip()
    if stack_clean in ("c#", "csharp", ".net", "dotnet"):
        target = "dotnet"
    elif stack_clean in ("java", "spring"):
        target = "java"
    elif stack_clean in ("node", "nodejs", "typescript", "javascript", "react"):
        target = "node"
    elif stack_clean in ("python", "fastapi", "django"):
        target = "python"
    else:
        target = "ai"

    archetypes_dir = Path(__file__).resolve().parent.parent / "templates" / "archetypes"
    tex_file = archetypes_dir / f"{target}.tex"
    if tex_file.exists():
        return tex_file.read_text(encoding="utf-8")

    fallback = Path(__file__).resolve().parents[3] / "Tarun_Mannava_Resume.tex"
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")
    return ""


def enforce_section_order_for_stack(latex: str, target_stack: str) -> str:
    """
    Enforces canonical archetype section ordering:
    - AI: PROJECTS before EXPERIENCE (agentic project work is the primary evidence for AI roles)
    - Every other stack: EXPERIENCE before PROJECTS
    """
    projects_first = (target_stack or "").lower().strip() == "ai"

    proj_match = re.search(
        r"(\\section\{(?:PROJECTS|TECHNICAL PROJECTS)\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    exp_match = re.search(
        r"(\\section\{(?:EXPERIENCE|Work Experience)\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if not proj_match or not exp_match:
        return latex

    proj_start, proj_end = proj_match.span(1)
    exp_start, exp_end = exp_match.span(1)

    proj_block = proj_match.group(1).strip()
    exp_block = exp_match.group(1).strip()

    # Swap only when the order is wrong for this stack and the two blocks do not overlap.
    if projects_first and exp_start < proj_start and exp_end <= proj_start:
        middle = latex[exp_end:proj_start].strip()
        new_combined = proj_block + "\n\n" + middle + ("\n\n" if middle else "") + exp_block
        latex = latex[:exp_start] + new_combined + "\n\n" + latex[proj_end:]
    elif not projects_first and proj_start < exp_start and proj_end <= exp_start:
        middle = latex[proj_end:exp_start].strip()
        new_combined = exp_block + "\n\n" + middle + ("\n\n" if middle else "") + proj_block
        latex = latex[:proj_start] + new_combined + "\n\n" + latex[exp_end:]

    return latex


def clean_professional_title(raw_title: str, target_stack: str = "python") -> str:
    """Normalizes any messy JD title into a clean, standard professional engineering title.
    Never allows raw recruiter suffixes like '- Ruby', ', Manufacturing Systems', '(Starlink)'.
    """
    canonical_for_stack = {
        "python": "Software Developer",
        "java": "Software Engineer",
        "dotnet": ".NET Software Engineer",
        "node": "Full Stack Software Engineer",
        "ai": "AI Engineer",
    }
    default_title = canonical_for_stack.get(target_stack.lower(), "Software Engineer")

    if not raw_title:
        return default_title

    raw_lower = raw_title.lower()
    if target_stack == "ai" and any(w in raw_lower for w in ["ai", "machine learning", "ml", "learning", "reinforcement", "genai", "llm", "vision", "nlp"]):
        return "AI Engineer"

    cleaned = raw_title.strip()
    # Strip parenthetical annotations: "Software Engineer (Starlink Ground Network)" -> "Software Engineer"
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    # Strip after hyphens or en-dashes: "Software Engineer - Ruby" -> "Software Engineer"
    cleaned = re.split(r"\s+[-–—]\s+", cleaned)[0].strip()
    # Strip after commas: "Full Stack Software Engineer, Manufacturing Systems" -> "Full Stack Software Engineer"
    cleaned = re.split(r",", cleaned)[0].strip()
    # Strip trailing punctuation
    cleaned = cleaned.strip(" -–—,./")

    lower = cleaned.lower()
    if "full stack" in lower or "fullstack" in lower:
        return "Full Stack Software Engineer"
    elif "ai" in lower or "machine learning" in lower or "ml" in lower:
        return "AI Engineer" if target_stack == "ai" else "Software Engineer"
    elif "backend" in lower:
        return "Backend Software Engineer"
    elif "frontend" in lower:
        return "Frontend Software Engineer"
    elif ".net" in lower or "c#" in lower:
        return ".NET Software Engineer"
    elif "developer" in lower:
        return "Software Developer"
    elif "engineer" in lower:
        return "Software Engineer"

    return default_title


def enforce_clean_header_title(
    latex: str | None,
    target_stack: str = "python",
    role_name: str | None = None,
) -> str | None:
    """Ensures the bold role-title in the LaTeX header under candidate name is a clean,
    standard professional title and never contains raw JD noise or weird suffixes.
    """
    if not latex:
        return latex

    pattern = re.compile(
        r"(\{\\Huge\s*\\textbf\{[^\}]+\}\}\s*\\\\(?:\[\d+pt\])?\s*\n\s*\\textbf\{)([^}]+)(\}\s*\\\\(?:\[\d+pt\])?)",
        re.IGNORECASE,
    )
    m = pattern.search(latex)
    if not m:
        return latex

    current_title = m.group(2).strip()
    clean_title = clean_professional_title(role_name or current_title, target_stack)
    if current_title != clean_title:
        latex = latex[:m.start()] + f"{m.group(1)}{clean_title}{m.group(3)}" + latex[m.end():]
    return latex


CANONICAL_SUMMARIES: dict[str, str] = {
    "dotnet": r"\textit{Full Stack Software Engineer with 3+ years of experience specializing in C\#, .NET 6/8 and ASP.NET Core, and distributed systems alongside modern React frontends. Experienced in enterprise Web APIs, Entity Framework Core optimization, SQL Server architectures, Azure and AWS cloud services, and building AI-in-the-loop solutions with custom AI skills and automated evaluation pipelines.}",
    "java": r"\textit{Full Stack Software Engineer with 3+ years of experience building high-throughput microservices in Java 11/17 and Spring Boot alongside responsive React/TypeScript frontends. Proven track record in relational and NoSQL database optimization (PostgreSQL, MongoDB, SQL Server), event-driven messaging with RabbitMQ, and building AI-assisted solutions with AI-in-the-loop validation and custom AI skills.}",
    "python": r"\textit{Full Stack Software Developer with 3+ years of experience building asynchronous backend microservices in Python 3.10+, FastAPI, and React frontends. Proven expertise in relational and NoSQL data modeling (SQLAlchemy, PostgreSQL, MongoDB), background task pipelines with RabbitMQ and Redis, and building production AI solutions with AI-in-the-loop workflows.}",
    "node": r"\textit{AI \& Software Engineer with 4+ years of experience building scalable backend services and production agentic AI systems across Node.js, Python, and AWS. Specializing in multi-agent orchestration (Claude Code, LangGraph, CrewAI, AWS Bedrock), Model Context Protocol (MCP) server development, and developer productivity tooling, with hands-on experience in custom agent harnesses, enterprise API integrations, human-in-the-loop workflows, and LLM observability with LangSmith and CloudWatch.}",
    "ai": r"\textit{AI \& Software Engineer with 4+ years of experience building production LLM systems and scalable backend services. Specializing in LangGraph multi-agent orchestration, Model Context Protocol (MCP) tool integration, agentic and corrective RAG, and LangSmith evaluation pipelines, on a foundation of high-throughput Java and Python microservices, PostgreSQL, Redis caching, and AWS.}",
}


def normalize_summary_placement(latex: str | None, target_stack: str = "python") -> str | None:
    r"""Ensures the candidate summary is always preserved, correctly formatted as an italicized
    paragraph inside \begin{center}...\end{center}, and never orphaned or dropped under a
    separate \section{SUMMARY} block.
    """
    if not latex:
        return latex

    clean_stack = (target_stack or "python").lower().strip()
    if clean_stack not in CANONICAL_SUMMARIES:
        clean_stack = "python"
    default_summary = CANONICAL_SUMMARIES[clean_stack]

    extracted_summary: str | None = None

    # Check if a \section{SUMMARY} or \section{PROFESSIONAL SUMMARY} exists
    sec_match = re.search(
        r"(\\section\{(?:PROFESSIONAL\s+)?SUMMARY\}\s*)(.*?)(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if sec_match:
        content = sec_match.group(2).strip()
        # Clean up any \small or list environments
        content = re.sub(r"\\begin\{(?:itemize|center)\}[^}]*", "", content)
        content = re.sub(r"\\end\{(?:itemize|center)\}", "", content)
        content = re.sub(r"\\item\b", "", content)
        content = re.sub(r"\\small\b", "", content)
        content = content.strip(" {}\n\r\t")
        if content:
            if content.startswith(r"\textit{") and content.endswith("}"):
                extracted_summary = content
            else:
                extracted_summary = f"\\textit{{{content}}}"
        # Remove the \section{SUMMARY} block from the body
        latex = latex[: sec_match.start(0)] + latex[sec_match.end(0) :]

    # Verify or inject summary in \begin{center}...\end{center}
    center_match = re.search(r"(\\begin\{center\}.*?\\end\{center\})", latex, re.DOTALL)
    if center_match:
        center_block = center_match.group(1)
        summary_to_use = extracted_summary or default_summary

        it_match = re.search(
            r"\\textit\{[^{}]*(?:experience|engineer|developer|building)[^{}]*\}",
            center_block,
            re.IGNORECASE,
        )
        if it_match:
            if extracted_summary:
                new_center = (
                    center_block[: it_match.start(0)]
                    + extracted_summary
                    + center_block[it_match.end(0) :]
                )
                latex = (
                    latex[: center_match.start(1)]
                    + new_center
                    + latex[center_match.end(1) :]
                )
        else:
            end_center_idx = center_block.rfind(r"\end{center}")
            if end_center_idx != -1:
                before_end = center_block[:end_center_idx].rstrip()
                if not before_end.endswith(r"\\[4pt]") and not before_end.endswith(r"\\"):
                    before_end += r" \\[4pt]"
                new_center = (
                    before_end + "\n  " + summary_to_use + "\n" + center_block[end_center_idx:]
                )
                latex = (
                    latex[: center_match.start(1)]
                    + new_center
                    + latex[center_match.end(1) :]
                )

    return latex


def rewrite_resume(request: RewriteRequest) -> RewriteResponse:
    target_stack = detect_target_stack(
        request.job_description,
        user_override=request.target_stack or request.selected_stack_override,
        role_name=request.role_name,
        company_context=request.company_context,
    )

    original_input_latex = request.resume_latex

    # Route to canonical archetype template if incoming LaTeX is default,
    # or lacks the target archetype's signature structure.
    archetype_latex = get_archetype_latex(target_stack)
    if archetype_latex:
        is_tarun_base = "Tarun Mannava" in request.resume_latex or "tarun" in request.resume_latex.lower()
        is_default_or_old = (
            (is_tarun_base and target_stack == "ai" and "ProofStack" not in request.resume_latex)
            or (is_tarun_base and target_stack == "node" and "ProofStack" not in request.resume_latex)
            or (is_tarun_base and target_stack in ("java", "dotnet") and "Behavioral Health" not in request.resume_latex)
            or (is_tarun_base and target_stack == "python" and "FastAPI" not in request.resume_latex)
            or len(request.resume_latex.strip()) == 0
        )
        if is_default_or_old:
            request.resume_latex = archetype_latex

    resume_text = latex_to_text(request.resume_latex)
    job_keywords = extract_keywords(
        request.job_description + "\n" + (request.company_context or ""),
        job_context=True,
    )
    initial_score = score_keywords(
        job_keywords,
        resume_text,
        target_threshold=request.target_match_threshold,
        rewrite_mode=request.rewrite_mode,
        confirmed_skills=request.confirmed_skills,
    )

    industry = request.selected_industry or "General Technology"

    missing_terms = [kw.term for kw in initial_score.missing_keywords]
    unsupported_terms = [kw.term for kw in initial_score.unsupported_keywords]

    prompt = build_user_prompt(
        request=request,
        missing_terms=missing_terms,
        unsupported_terms=unsupported_terms,
        target_stack=target_stack,
        industry=industry,
    )

    res = generate_rewrite(prompt, request.align_titles)
    generated_text = res[0]
    provider = res[1]
    provider_err = res[2] if len(res) > 2 else None

    if not generated_text:
        warnings = list(initial_score.warnings)
        err_msg = f": {provider_err}" if provider_err else ""
        warnings.append(
            f"AI provider '{provider}' is not configured correctly{err_msg}, so the API returned the original LaTeX with analysis only."
        )
        return RewriteResponse(
            rewritten_latex=original_input_latex,
            match_score=initial_score.match_score,
            target_met=initial_score.target_met,
            matched_keywords=initial_score.matched_keywords,
            missing_keywords=initial_score.missing_keywords,
            unsupported_keywords=initial_score.unsupported_keywords,
            warnings=warnings,
            changes_made=[
                f"No rewrite performed because AI provider '{provider}' could not generate content."
            ],
        )

    rewritten = generated_text.strip()
    # Strip markdown fences if AI wrapped it
    if rewritten.startswith("```"):
        lines = rewritten.splitlines()
        if len(lines) >= 2:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            rewritten = "\n".join(lines).strip()

    # Balance LaTeX environments & custom lists
    rewritten = repair_truncated_latex(rewritten)

    # Strip inline bolding from bullets
    rewritten = remove_inline_bolding_from_bullets(rewritten)

    # Sanitize unescaped % and special characters in bullets/body
    rewritten = sanitize_latex_escaping(rewritten)

    # Clean any accidental GitHub Actions or CI/CD mentions from Cognizant
    rewritten = clean_cognizant_guardrails(rewritten)

    # If target stack is Java, ensure Cognizant appears after USF and adapt USF to Java
    if target_stack == "java":
        rewritten = adapt_resume_for_java(rewritten, request)

    # If target stack is .NET, strictly enforce C#/.NET 8 in Cognizant, USF, Skills, and Summary
    if target_stack == "dotnet":
        rewritten = adapt_resume_for_dotnet(rewritten, request)

    # If target stack is Node, ensure NODE_STACK_SKILLS are applied
    if target_stack == "node":
        rewritten = adapt_resume_for_node(rewritten, request)

    # Enforce strict reverse-chronological Experience order (USF -> Cognizant) across all stacks
    rewritten = enforce_reverse_chronological_experience(rewritten)

    # Enforce canonical archetype section order (AI: Projects first; all other stacks: Experience first)
    rewritten = enforce_section_order_for_stack(rewritten, target_stack)

    # Enforce clean standard professional headline (never raw JD noise like "Software Engineer - Ruby")
    rewritten = enforce_clean_header_title(rewritten, target_stack, request.role_name)

    # Ensure professional summary is properly placed in \begin{center} and never dropped
    rewritten = normalize_summary_placement(rewritten, target_stack)

    # Sanitize banned skills in skills section if provided
    if request.banned_skills:
        from .latex_skills import sanitize_skills_section
        from .project_framing import extract_resume_supported_terms
        supported = extract_resume_supported_terms(latex_to_text(request.resume_latex))
        rewritten = sanitize_skills_section(
            rewritten,
            supported,
            request.confirmed_skills,
            "backend_engineer",
            request.resume_latex,
            banned_skills=request.banned_skills,
        )

    # Preserve certifications section from original resume
    rewritten = preserve_certifications_section(request.resume_latex, rewritten)

    # Update location if target_location was provided
    if request.target_location:
        rewritten = update_contact_location(rewritten, request.target_location)

    final_text = latex_to_text(rewritten)
    final_score = score_keywords(
        job_keywords,
        final_text,
        target_threshold=request.target_match_threshold,
        rewrite_mode=request.rewrite_mode,
        confirmed_skills=request.confirmed_skills,
    )

    changes = [
        f"Rewrote resume bullets, existing projects, headline, and skills using {provider}.",
        f"Target Stack: {target_stack.upper()}; Industry Context: {industry}.",
        f"Keyword match score changed from {initial_score.match_score}% to {final_score.match_score}%.",
    ]
    if request.target_location:
        changes.append(f"Updated contact location to '{request.target_location}'.")
    if request.align_titles:
        changes.append(f"Title alignment was ENABLED: job titles adjusted toward '{request.role_name or 'target role'}'.")

    return RewriteResponse(
        rewritten_latex=rewritten,
        match_score=final_score.match_score,
        target_met=final_score.target_met,
        matched_keywords=final_score.matched_keywords,
        missing_keywords=final_score.missing_keywords,
        unsupported_keywords=final_score.unsupported_keywords,
        warnings=list(final_score.warnings),
        changes_made=changes,
    )
