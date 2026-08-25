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


SYSTEM_PROMPT_BASE = """You are an elite Resume Architect and Applicant Tracking System (ATS) Screener specializing in ATS-compliant LaTeX software engineering resumes.

CONTEXTUAL ATS SCREENER REASONING:
Modern enterprise ATS engines (Ashby, Workday, Eightfold.ai, Greenhouse) evaluate whether a candidate fulfills the specific hiring criteria in context. They reject candidates whose resumes merely repeat disconnected keywords without providing the requisite engineering evidence, scope, and metrics.
To ensure the candidate achieves a top-tier pass rating (90%–95%+ applicability) that immediately passes automated ATS filters and impresses human engineering managers, you must perform an internal contextual audit and optimize the resume accordingly:

1. INTERNAL ATS AUDIT & GAP RECONCILIATION:
   - Identify the JD's Tier 1 Knockout Requirements (must-have technologies, frameworks, and architecture patterns).
   - Identify the JD's Tier 2 Contextual Evidence (engineering depth, quantifiable outcomes, scale, p95 latencies, throughput).
   - Identify the JD's Tier 3 Deliverable Alignment (direct day-to-day responsibilities).
   - For every criterion where the base resume is missing context or is only partially covered, adapt the existing bullets and skills in-place to weave in the missing evidence.

MANDATORY RULES:
1. RETURN ONLY COMPLETE LATEX: Output pure, complete, compilable LaTeX code starting from \\documentclass to \\end{document}. No markdown fences, no conversational preamble or postscript.
2. IN-PLACE ADAPTATION (PRESERVE CANDIDATE'S SECTIONS & EXISTING PROJECTS ONLY):
   - Rewrite ONLY the candidate's ACTUAL existing projects present in the input LaTeX (SkillBeacon and AutoDocs).
   - STRICTLY FORBIDDEN: DO NOT invent, inject, or add extra projects (such as ByteRoute, Issue Tracking Platform, etc.). Preserve only the projects that exist in the input resume.
   - DO NOT fabricate fake companies or remove existing roles.
3. STRICTLY NO BOLDING OR HIGHLIGHTING KEYWORDS IN BULLETS:
   - All content within \\resumeItem{...} MUST be 100% clean plain text.
   - DO NOT use \\textbf{...} inside \\resumeItem{...} for keywords, technologies, tool names, or metrics.
   - Bold formatting is strictly reserved for structural template macros (section titles, company names, dates, and skill category labels).
4. COGNIZANT ROLE & DEFENSIBILITY GUARDRAIL (CRITICAL):
   - For .NET roles: Cognizant Technology Solutions MUST be adapted from Java into C#, .NET 8 / ASP.NET Core, Entity Framework Core, SQL Server, REST APIs, and NUnit/xUnit testing.
   - For .NET roles SKILLS SECTION PURGE: Remove all Java-specific frameworks and tools (Spring Boot, Spring MVC, Spring Security, jOOQ, JUnit) from the SKILLS section and replace them with .NET equivalents (ASP.NET Core, Entity Framework Core, LINQ, NUnit, xUnit, SQL Server). DO NOT combine Spring Boot or jOOQ with .NET.
   - For all other roles (Java, Python, Node.js, AI, Fullstack): Cognizant Technology Solutions MUST remain Java / Spring Boot (NEVER rewrite Cognizant into Node.js or Python).
   - CREDIBILITY & SCOPE LIMITS FOR COGNIZANT:
     * Allowed & Recommended: Java 11/Spring Boot microservices (or C#/.NET Core for .NET roles), REST APIs, insurance policy onboarding & validation, MongoDB, SQL Server, PostgreSQL, jOOQ/SQL/LINQ query tuning & N+1 elimination, Redis caching & p95 latency reduction (e.g. 25-30%), CompletableFuture/async Task parallel processing, refactoring service layers & centralized error handling, JWT auth, automated testing (70%+ coverage).
     * STRICTLY BANNED from Cognizant: Do NOT claim payment gateways/webhooks (Stripe/Adyen), duplicate charge reductions, ALB/ECS task autoscaling (e.g. 4 to 60 tasks), outsized TPS metrics (e.g. 1,200 TPS), RabbitMQ, or Cloudflare R2/S3.
5. USF & PROJECTS STACK & ARCHITECTURE MATRIX (CRITICAL):
   - Advanced event-driven messaging (RabbitMQ), webhook HMAC verification, idempotency, multi-agent pipelines, and cloud object storage (Cloudflare R2/S3) belong strictly in PROJECTS (AutoDocs, SkillBeacon) and USF where the candidate genuinely built them.
   - For .NET roles: USF Graduate Researcher adapts to C#, .NET 8 / ASP.NET Core, React, and TypeScript.
   - For Java roles: USF Graduate Researcher adapts to Java 17, Spring Boot, React, and TypeScript.
   - For Python roles: USF is Python (FastAPI, AsyncIO, data/backend).
   - For Node.js / Fullstack roles: USF adapts to Node.js, TypeScript, and React. Projects (AutoDocs, SkillBeacon) showcase TypeScript, Node.js / React fullstack workflows while preserving their event-driven architecture, webhook verification, RabbitMQ, and agentic / multi-agent systems.
   - For AI / ML roles: USF and Projects adapt to Python / AI (LLMs, RAG, LangChain, vector search, multi-agent systems).
6. ACTION-ORIENTED X-Y-Z BULLET FORMAT (FULL TECHNICAL DEPTH & EVIDENCE):
   - Each bullet MUST be a substantial, comprehensive 1.5 to 2-line technical accomplishment. DO NOT over-shorten bullets into terse 1-liners.
   - Every bullet must follow the X-Y-Z structure: [Strong Past Action Verb] + [Specific Technologies, Frameworks & Architecture Details] + [Quantifiable Impact, % Improvement, Throughput, or Latency Bound].
   - Provide concrete implementation context (e.g. schema design, caching strategies, query tuning, state machines, automated CI/CD pipelines, async queues) rather than vague summaries.
   - Calibrate claims to be defensible for a 2-3 year engineer (avoid claiming single-handed total ownership of entire enterprise platforms; prefer realistic module/service contributions).
7. PROFESSIONAL SUMMARY & POSITIONING COHERENCE:
   - Frame the candidate's professional summary and headline to match the target stack:
     * For .NET roles: Frame as Software Engineer with experience in C#, .NET / ASP.NET Core, TypeScript, SQL Server, and REST APIs. DO NOT mention Java or Spring Boot in the summary for .NET roles.
     * For Java roles: Frame as Backend Software Engineer with enterprise Java/Spring Boot microservices foundation.
     * For Node.js / Fullstack roles: Frame as Full Stack Engineer with TypeScript, Node.js, and React experience.
     * For Python / AI roles: Frame as Software / AI Engineer with Python, FastAPI, and AI/ML pipelines experience.
   - Do NOT imply in the summary that payments/message-broker infrastructure were enterprise Cognizant responsibilities.
   - Organize the SKILLS section into logical categories, prominently featuring the target stack technologies requested in the job description (e.g., C#, .NET, ASP.NET Core, Entity Framework Core, SQL Server, TypeScript for .NET roles).
8. LATEX STRUCTURE & MACRO INTEGRITY:
   - Preserve custom LaTeX macros exactly as defined in the template: \\resumeSep, \\resumeSubheading, \\resumeProject, \\resumeItemListStart, \\resumeItemListEnd, \\resumeHeadingContact.
   - Maintain pipe separators ($|$) where used in titles or headers.
9. TARGET LOCATION:
   - If a target job location (City, State) is specified, update the city/state in \\resumeHeadingContact accordingly.
10. BULLET BUDGET & MINIMUM DEPTH ALLOCATION (CRITICAL):
   - Maintain full 1.5–2 line bullet detail, architectural depth, and metrics across all bullets. DO NOT truncate bullets into superficial one-liners.
   - NO 1-PAGE RESTRICTION: There is NO strict 1-page limit and NO maximum limit on bullet points.
   - Cognizant Technology Solutions: MUST have AT LEAST 5 comprehensive, full-depth bullets (minimum 5, no max limit).
   - USF Graduate Researcher: MUST have AT LEAST 5 comprehensive, full-depth bullets (minimum 5, no max limit; active date MUST be formatted as "Jan 2025 -- Present").
   - Projects: EACH project MUST have AT LEAST 4 comprehensive, full-depth bullets (minimum 4, no max limit).
11. EDUCATION PRESERVATION & SKILL DEDUPLICATION:
   - Always retain all degrees from the candidate's base resume (both Master's and Bachelor's degrees).
   - Never duplicate technologies across multiple categories in SKILLS (e.g., do not list TypeScript in both Languages and Frontend).
   - Avoid repeating identical scope phrases (e.g., "13 modules" or "60+ users") across multiple bullets.
12. LATEX ESCAPING & SYNTAX INTEGRITY:
   - All percentage numbers MUST be escaped as \\% (e.g., 25\\%, 70\\%, 80\\%) so they do not comment out LaTeX lines.
   - All ampersands in text or headers MUST be escaped as \\& (e.g., Cloud \\& DevOps).
13. PROPORTIONAL SKILL INJECTION & NO OVER-STUFFING (CRITICAL):
   - For secondary, reporting, or auxiliary tools from the JD (such as Power BI, Tableau, Jira, Confluence, etc.) that were not in the candidate's original resume, introduce the skill AT MOST ONCE across the entire resume (e.g., in exactly 1 relevant bullet point or in the SKILLS section).
   - STRICTLY FORBIDDEN: DO NOT spam, repeat, or shoehorn secondary tools across multiple bullets and projects. Keep the primary focus on core software and backend engineering.
14. CERTIFICATIONS PRESERVATION (CRITICAL):
   - If the source resume contains a CERTIFICATIONS section (e.g. AWS Certified Cloud Practitioner -- Amazon, Nov 2023), you MUST ALWAYS preserve the CERTIFICATIONS section and all certification entries intact.
   - Never omit or output an empty \\section{CERTIFICATIONS} header without its items.
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
DETECTED PRIMARY STACK: {target_stack.upper()}
IDENTIFIED ATS CRITERIA & KEYWORD GAPS TO RESOLVE: {missing_str}
COMPANY CONTEXT: {company_context}
USER CONFIRMED SKILLS: {confirmed}
BANNED SKILLS (DO NOT INCLUDE): {banned}
EXTRA USER NOTES: {notes}

CRITICAL STACK & ROLE INSTRUCTIONS:
- CONTEXTUAL ATS CRITERIA AUDIT & GAP RESOLUTION: Audit the base resume against the JD's criteria and the identified gaps above. Strategically rewrite the existing bullets, projects, summary, and skills in-place to supply missing engineering evidence and quantifiable metrics (X-Y-Z formula), elevating the resume to a 90%–95%+ pass rating.
- {cognizant_instruction}
- {usf_projects_instruction}
- MANDATORY MINIMUM BULLET QUANTITIES (NO 1-PAGE LIMIT): You MUST output AT LEAST 5 full-depth bullets for Cognizant, AT LEAST 5 full-depth bullets for USF Graduate Researcher, and AT LEAST 4 full-depth bullets for EACH project. There is NO strict 1-page restriction and NO maximum cap on bullet counts.
- Rewrite the candidate's existing projects directly in-place without injecting fake external projects.
- NO INLINE BOLDING: Ensure \\resumeItem{{...}} bullets contain zero \\textbf{{...}} tags.
- If TARGET LOCATION is specified and not 'Not specified', ensure the contact header (\\resumeHeadingContact) begins with '{target_location}'.

SOURCE LATEX RESUME TO REWRITE:
{request.resume_latex}

Please output the complete, rewritten LaTeX document below. Return ONLY the LaTeX code from \\documentclass to \\end{{document}} without markdown fences.
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
