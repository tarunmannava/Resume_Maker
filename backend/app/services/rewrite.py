import re
import logging
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
    "Backend & Frameworks": ["Spring Boot", "Spring MVC", "Spring Security", "Spring Data JPA", "Hibernate", "REST APIs", "Microservices"],
    "Messaging & Caching": ["RabbitMQ", "Redis", "CompletableFuture", "ExecutorService"],
    "Databases & Cloud": ["PostgreSQL", "MongoDB", "SQL Server", "MySQL", "AWS (EC2, S3, RDS)", "Docker", "GitHub Actions", "Linux"],
    "AI Developer Tools": ["Claude Code", "Cursor", "GitHub Copilot", "RAG", "Prompt Engineering"],
    "Testing & Tools": ["JUnit 5", "Mockito", "Postman", "Maven", "Gradle", "React"]
  },
  "DOTNET_STACK_SKILLS": {
    "Languages & Core": ["C#", ".NET 8 / .NET Core", "ASP.NET Core", "Entity Framework Core", "LINQ", "SQL", "Python", "JavaScript"],
    "Backend & APIs": ["RESTful APIs", "Web API", "Microservices", "RabbitMQ", "Redis Caching", "OAuth2", "Azure AD"],
    "Databases & Cloud": ["SQL Server (T-SQL)", "PostgreSQL", "MongoDB", "Azure (App Services, DevOps)", "Docker", "CI/CD", "Git"],
    "AI Developer Tools": ["Claude Code", "Cursor", "GitHub Copilot", "RAG", "Prompt Engineering"],
    "Testing & Frontend": ["xUnit", "NUnit", "Moq", "Postman", "React", "HTML5", "CSS3"]
  },
  "PYTHON_STACK_SKILLS": {
    "Languages": ["Python (3.10+)", "SQL", "Java", "TypeScript", "JavaScript", "Bash"],
    "Backend & APIs": ["FastAPI", "Flask", "Django", "Pydantic", "AsyncIO", "REST APIs", "Microservices"],
    "Messaging & Data": ["RabbitMQ", "Redis", "PostgreSQL", "MySQL", "MongoDB", "SQLAlchemy", "Alembic"],
    "Cloud & DevOps": ["AWS (ECS, Lambda, S3)", "Docker", "GitHub Actions", "CI/CD Pipelines", "Linux", "Nginx"],
    "AI Developer Tools": ["Claude Code", "Cursor", "GitHub Copilot", "RAG", "Prompt Engineering"],
    "Testing & Frontend": ["pytest", "unittest", "Postman", "Swagger", "React", "Next.js"]
  },
  "NODE_STACK_SKILLS": {
    "Languages": ["TypeScript", "JavaScript (ES2022+)", "Python", "Java", "SQL", "HTML5", "CSS3"],
    "Backend & APIs": ["Node.js", "Express.js", "NestJS", "REST APIs", "GraphQL", "WebSocket / Socket.io", "Microservices"],
    "Frontend": ["React 18", "Next.js", "Redux Toolkit", "React Query", "Tailwind CSS"],
    "Messaging & Storage": ["RabbitMQ", "Redis (Pub/Sub, Caching)", "PostgreSQL", "MongoDB", "Prisma ORM"],
    "AI Developer Tools": ["Claude Code", "Cursor", "GitHub Copilot", "RAG", "Prompt Engineering"],
    "DevOps & Testing": ["AWS (S3, CloudFront)", "Docker", "GitHub Actions", "Jest", "Supertest", "OAuth2", "JWT"]
  },
  "AI_STACK_SKILLS": {
    "Languages": ["Python", "SQL", "TypeScript", "Java"],
    "GenAI & LLM Frameworks": ["LangChain", "LlamaIndex", "LangGraph", "RAG Pipelines", "Multi-Agent Systems", "Prompt Engineering"],
    "Vector DBs & Search": ["Pinecone", "Qdrant", "ChromaDB", "Semantic Search", "Hybrid Search", "Embeddings"],
    "Backend & Messaging": ["FastAPI", "AsyncIO", "RabbitMQ", "Redis", "REST APIs", "PostgreSQL", "MongoDB"],
    "AI Developer Tools": ["Claude Code", "Cursor", "GitHub Copilot", "OpenAI Codex", "Weights & Biases", "MLflow"],
    "Cloud & MLOps": ["AWS", "Docker", "Kubernetes", "GitHub Actions", "CI/CD", "Prometheus", "Grafana"]
  }
}

MANDATORY OPERATIONAL RULES:
1. OUTPUT: Return pure compilable LaTeX starting from \documentclass to \end{document}. No markdown fences (no ```latex), no conversational text.
2. IN-PLACE PRESERVATION (PROJECTS & EXPERIENCE):
   - Rewrite ONLY the candidate's actual existing projects (SkillBeacon and AutoDocs).
   - STRICTLY FORBIDDEN: Do NOT invent or inject fake external projects (such as ByteRoute, Issue Tracker, etc.).
   - Preserve candidate companies and degrees (Master's and Bachelor's).
3. CLEAN BULLETS (ZERO INLINE BOLDING):
   - All text inside \resumeItem{...} MUST be 100% clean plain text. ZERO \textbf{...} tags inside bullet items.
4. ACTION-ORIENTED X-Y-Z BULLET DEPTH (MINIMUM BUDGETS):
   - Each bullet must be 1.5–2 lines: [Strong Action Verb] + [Specific Technologies & Architecture] + [Quantifiable Impact / Metrics / Latency].
   - NO 1-page restriction. Output at least 5 bullets for Cognizant, at least 5 for USF Graduate Researcher, and at least 4 for each project.
5. STACK-SPECIFIC EXPERIENCE & SKILLS RULES:
   - For .NET roles: Adapt Cognizant and USF to C#, .NET 8 / ASP.NET Core, Entity Framework Core, SQL Server, MongoDB, and xUnit/NUnit. Use DOTNET_STACK_SKILLS (strictly purge Java/Spring from SKILLS).
   - For Java roles: Preserve Cognizant as Java 11 / Spring Boot microservices with MongoDB/SQL Server (order Cognizant before USF). Adapt USF to Java 17 / Spring Boot. Use JAVA_STACK_SKILLS.
   - For Python, Node.js, and AI roles: Retain Cognizant as Java 11 / Spring Boot enterprise microservices foundation. Use PYTHON_STACK_SKILLS, NODE_STACK_SKILLS, or AI_STACK_SKILLS respectively.
6. SYNTAX INTEGRITY:
   - Escape all percentages as \% (e.g. 30\%, 70\%) and ampersands as \& (e.g. Cloud \& DevOps).
   - Always preserve CERTIFICATIONS section if present in the base resume.
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
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (.NET / C# TARGET STACK - MANDATORY): Adapt Cognizant Technology Solutions from Java to C#, .NET 8 / ASP.NET Core, "
            "Entity Framework Core, SQL Server, REST APIs, and NUnit/xUnit testing. "
            "SKILLS PURGE: Remove all Java-specific frameworks and tools (Spring Boot, Spring MVC, Spring Security, jOOQ, JUnit) from the SKILLS section "
            "and replace them entirely with .NET/C# technologies: C#, .NET 8, ASP.NET Core, Entity Framework Core, LINQ, SQL Server, TypeScript, NUnit, xUnit. "
            "DO NOT combine Spring Boot with .NET."
        )
        usf_projects_instruction = (
            "USF & PROJECTS RULE (.NET): Adapt USF Graduate Researcher to C#, .NET 8, ASP.NET Core Web API, React, and TypeScript. "
            "Projects (SkillBeacon, AutoDocs) keep their core architecture without adding fake external projects."
        )
    elif target_stack == "java":
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (JAVA TARGET STACK): Cognizant Technology Solutions MUST be Java / Spring Boot, "
            "Microservices, REST APIs, and SQL/PostgreSQL."
        )
        usf_projects_instruction = (
            "USF & PROJECTS RULE (JAVA): Adapt USF Graduate Researcher to Java 17, Spring Boot, React, and TypeScript. "
            "Projects (SkillBeacon, AutoDocs) keep their core architecture without adding fake external projects."
        )
    elif target_stack == "node":
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (NODE.JS TARGET STACK): Cognizant Technology Solutions MUST remain Java / Spring Boot "
            "(do NOT change to Node.js)."
        )
        usf_projects_instruction = (
            "USF & PROJECTS (NODE.JS): Adapt USF Graduate Researcher to Node.js, TypeScript, and React. "
            "In Projects, showcase TypeScript, Node.js / React full-stack integration while PRESERVING AutoDocs's "
            "agentic multi-agent architecture, event-driven webhooks, and RabbitMQ pipeline."
        )
    elif target_stack == "ai":
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (AI / ML TARGET STACK): Cognizant Technology Solutions MUST remain Java / Spring Boot."
        )
        usf_projects_instruction = (
            "USF & PROJECTS (AI): Adapt USF Graduate Researcher and Projects to Python / AI (LLMs, RAG pipelines, "
            "LangChain, vector search, multi-agent systems)."
        )
    else:  # python
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (PYTHON TARGET STACK): Cognizant Technology Solutions MUST remain Java / Spring Boot "
            "(do NOT change to Python)."
        )
        usf_projects_instruction = (
            "USF & PROJECTS (PYTHON): USF Graduate Researcher and Projects MUST BE Python, FastAPI, AsyncIO, "
            "data/backend architectures, and agents."
        )

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
- {cognizant_instruction}
- {usf_projects_instruction}
- In-place adaptation: Adapt existing bullets & projects directly to answer the JD's criteria (X-Y-Z formula) without adding fake external projects.
- Clean bullets: Pure plain text with ZERO \\textbf{{...}} inside \\resumeItem{{...}}.
- Minimum bullet depth: Output at least 5 bullets for Cognizant, at least 5 for USF, and at least 4 for each project.
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
    kwargs = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": build_system_prompt(align_titles)},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "top_p": 0.95,
        "max_tokens": settings.max_output_tokens,
    }
    if settings.openai_base_url and "nvidia.com" in settings.openai_base_url:
        kwargs["extra_body"] = {
            "chat_template_kwargs": {
                "thinking": True,
                "reasoning_effort": "high",
            }
        }
    elif settings.openai_base_url and "openrouter.ai" in settings.openai_base_url:
        kwargs["extra_headers"] = {"X-OpenRouter-Cache": "false"}
        kwargs["extra_body"] = {
            "reasoning": {
                "enabled": True
            }
        }
    completion = client.chat.completions.create(**kwargs)
    if completion.choices and len(completion.choices) > 0:
        return completion.choices[0].message.content, None
    return None, "OpenAI returned empty completion choices"


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


def reorder_experience_for_java(latex: str) -> str:
    """When target stack is Java, ensure Cognizant Technology Solutions is placed before University of South Florida."""
    exp_match = re.search(
        r"(\\section\{(?:EXPERIENCE|Work Experience)\}\s*(?:%[^\n]*\n\s*)*\\resumeSubHeadingListStart\s*)(.*?)(\s*\\resumeSubHeadingListEnd)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not exp_match:
        return latex

    header, body, footer = exp_match.groups()
    cog_pos = body.find("Cognizant Technology Solutions")
    usf_pos = body.find("University of South Florida")
    if cog_pos != -1 and usf_pos != -1 and cog_pos > usf_pos:
        entries = re.split(r"(?=\\resumeSubheading)", body)
        cog_entry = [e for e in entries if "Cognizant Technology Solutions" in e]
        other_entries = [e for e in entries if "Cognizant Technology Solutions" not in e]
        if cog_entry:
            reordered_body = "".join(cog_entry + other_entries).strip()
            return latex[: exp_match.start(0)] + header + "\n  " + reordered_body + "\n" + footer + latex[exp_match.end(0) :]
    return latex


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


DOTNET_COGNIZANT_BLOCK = r"""  \resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \resumeItemListStart
    \resumeItem{Developed scalable C\# and .NET 8 / ASP.NET Core microservices for insurance policy onboarding, validation, and customer transactions, supporting distributed services handling 20K+ peak hourly requests.}
    \resumeItem{Engineered asynchronous validation and enrichment pipelines using async/await and Task Parallel Library (TPL), improving transaction processing latency through parallel task execution.}
    \resumeItem{Implemented Redis-backed caching strategies and cache warm-up routines, reducing SQL Server read bottlenecks and improving p95 API response times by 30\% during peak onboarding cycles.}
    \resumeItem{Designed and optimized database interactions across SQL Server (T-SQL) and MongoDB using Entity Framework Core and indexed queries, eliminating N+1 query patterns and minimizing database round trips.}
    \resumeItem{Refactored validation and business logic across 6+ microservices into reusable .NET service components with centralized exception handling and standardized RESTful Web API error responses.}
    \resumeItem{Secured REST endpoints using ASP.NET Core Identity, JWT authentication, and role-based access control (RBAC), integrating with enterprise identity providers.}
    \resumeItem{Authored comprehensive automated test suites using xUnit, NUnit, and Moq covering business-critical paths, establishing 70\%+ backend test coverage and reducing production regressions.}
  \resumeItemListEnd"""

DOTNET_USF_BLOCK = r"""  \resumeSubheading
    {University of South Florida}{Graduate Researcher, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Architected and deployed a production AI \& Health Literacy web platform for USF SHIELD Lab across 13 interactive modules in React and TypeScript, serving 60+ biomedical students and faculty.}
    \resumeItem{Engineered an ASP.NET Core (C\#) Web API backend and real-time dual-model sandbox integrating Groq and Hugging Face LLM APIs, featuring semantic grading rubrics, milestone detection, and response caching under 2s latency.}
    \resumeItem{Built an in-browser prompt evaluation engine using Transformers.js (WASM / ONNX) and TypeScript for local cosine similarity embedding scoring, providing zero-latency pedagogical feedback on prompt structure and constraints.}
    \resumeItem{Integrated OAuth2 (PKCE) session authentication and engineered PostgreSQL / SQL Server relational schemas with Entity Framework Core for secure access code verification, quiz scoring, and deterministic chat logging.}
  \resumeItemListEnd"""

JAVA_USF_BLOCK = r"""  \resumeSubheading
    {University of South Florida}{Graduate Researcher, Software Engineer}{Jan 2025}{May 2026}
  \resumeItemListStart
    \resumeItem{Architected and deployed a production AI \& Health Literacy web platform for USF SHIELD Lab across 13 interactive modules in React and TypeScript, serving 60+ biomedical students and faculty.}
    \resumeItem{Engineered a Java 17 and Spring Boot microservice backend with a real-time dual-model sandbox integrating Groq and Hugging Face LLM APIs, featuring semantic grading rubrics, milestone detection, and response caching under 2s latency.}
    \resumeItem{Built an in-browser evaluation engine using Transformers.js (WASM / ONNX) and TypeScript for local cosine similarity embedding scoring, providing zero-latency pedagogical feedback on prompt structure and constraints.}
    \resumeItem{Integrated OAuth2 (PKCE) session authentication and engineered PostgreSQL relational schemas with Spring Data JPA and Hibernate for secure access code verification, quiz scoring, and deterministic chat logging.}
  \resumeItemListEnd"""


def adapt_resume_for_dotnet(latex: str, request: RewriteRequest) -> str:
    """Strictly enforces C#/.NET 8 framing across Summary, Skills, Cognizant, and USF Experience."""
    # 1. Professional Summary guard
    center_match = re.search(r"(\\begin\{center\}.*?\\end\{center\})", latex, re.DOTALL)
    if center_match:
        center_text = center_match.group(1)
        if "Java" in center_text or "Spring" in center_text:
            dotnet_summary = (
                r"\textit{Software Engineer with 3+ years of experience building web applications and backend services in C\#, .NET, ASP.NET Core, Python, and FastAPI. "
                r"Skilled in REST APIs, microservices, asynchronous processing, relational databases, and AI-enabled applications.}"
            )
            new_center = re.sub(
                r"\\textit\{[^{}]*(?:Java|Spring)[^{}]*\}",
                lambda _m: dotnet_summary,
                center_text,
                flags=re.IGNORECASE,
            )
            if new_center == center_text:
                new_center = re.sub(r"\bJava\b", lambda _m: "C\\#", center_text)
                new_center = re.sub(r"\bSpring Boot\b", lambda _m: ".NET 8 / ASP.NET Core", new_center)
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
            if "Python" in usf_content or "Flask" in usf_content or "Django" in usf_content or ("C#" not in usf_content and ".NET" not in usf_content):
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
    # Reorder Cognizant before USF for Java roles
    latex = reorder_experience_for_java(latex)

    # USF Experience guard (adapt USF to Java/Spring Boot if still in Python/Flask)
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


def rewrite_resume(request: RewriteRequest) -> RewriteResponse:
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
    target_stack = detect_target_stack(
        request.job_description,
        user_override=request.selected_stack_override,
        role_name=request.role_name,
    )

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
            rewritten_latex=request.resume_latex,
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

    # If target stack is Java, ensure Cognizant appears before USF and adapt USF to Java
    if target_stack == "java":
        rewritten = adapt_resume_for_java(rewritten, request)

    # If target stack is .NET, strictly enforce C#/.NET 8 in Cognizant, USF, Skills, and Summary
    if target_stack == "dotnet":
        rewritten = adapt_resume_for_dotnet(rewritten, request)

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
