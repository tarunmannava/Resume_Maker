import re
import logging
from google import genai
from google.genai import types
from openai import OpenAI

from ..core.config import get_settings
from ..models.schemas import RewriteRequest, RewriteResponse
from .keyword_extractor import extract_keywords
from .latex import latex_to_text
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
2. IN-PLACE ADAPTATION (PRESERVE CANDIDATE'S SECTIONS & EXISTING PROJECTS):
   - Rewrite the candidate's ACTUAL existing experiences (USF Graduate Researcher, Cognizant SDE), existing projects (e.g., ByteRoute, Automated PR Documentation Agent / AutoDocs, SkillBeacon), summary/headline, and skills.
   - DO NOT fabricate fake companies, remove existing roles, or inject unrelated canned projects.
3. STRICTLY NO BOLDING OR HIGHLIGHTING KEYWORDS IN BULLETS:
   - All content within \\resumeItem{...} MUST be 100% clean plain text.
   - DO NOT use \\textbf{...} inside \\resumeItem{...} for keywords, technologies, tool names, or metrics.
   - Bold formatting is strictly reserved for structural template macros (section titles, company names, dates, and skill category labels).
4. COGNIZANT ROLE & DEFENSIBILITY GUARDRAIL (CRITICAL):
   - For .NET roles: Cognizant Technology Solutions is C# / .NET / ASP.NET Core, Entity Framework Core, and SQL Server.
   - For all other roles (Java, Python, Node.js, AI, Fullstack): Cognizant Technology Solutions MUST remain Java / Spring Boot (NEVER rewrite Cognizant into Node.js or Python).
   - CREDIBILITY & SCOPE LIMITS FOR COGNIZANT:
     * Allowed & Recommended: Java 11/Spring Boot microservices, REST APIs, insurance policy onboarding & validation, MongoDB, SQL Server, PostgreSQL, jOOQ/SQL query tuning & N+1 elimination, Redis caching & p95 latency reduction (e.g. 25-30%), CompletableFuture/ExecutorService parallel async processing, refactoring service layers & centralized error handling, Spring Security JWT auth, JUnit/Cucumber testing (70%+ coverage).
     * STRICTLY BANNED from Cognizant: Do NOT claim payment gateways/webhooks (Stripe/Adyen), duplicate charge reductions, ALB/ECS task autoscaling (e.g. 4 to 60 tasks), outsized TPS metrics (e.g. 1,200 TPS), RabbitMQ, or Cloudflare R2/S3.
5. USF & PROJECTS STACK & ARCHITECTURE MATRIX (CRITICAL):
   - Advanced event-driven messaging (RabbitMQ), webhook HMAC verification, idempotency, multi-agent pipelines, and cloud object storage (Cloudflare R2/S3) belong strictly in PROJECTS (AutoDocs, SkillBeacon) and USF where the candidate genuinely built them.
   - For .NET roles: USF and Projects MUST STAY Python (Python, FastAPI, React, multi-agent workflows).
   - For Java roles: USF and Projects MUST STAY Python (Python, FastAPI, React, multi-agent workflows).
   - For Python roles: USF and Projects MUST BE Python (FastAPI, AsyncIO, data/backend).
   - For Node.js / Fullstack roles: USF and Projects adapt to Node.js / TypeScript / React.
   - For AI / ML roles: USF and Projects adapt to Python / AI (LLMs, RAG, LangChain, vector search).
6. ACTION-ORIENTED X-Y-Z BULLET FORMAT:
   - Each bullet must start with a strong past-tense action verb (Developed, Implemented, Built, Optimized, Engineered, Configured, Integrated, Automated).
   - Integrate specific technologies inline within the accomplishment narrative.
   - Ground accomplishments with quantifiable metrics (% improvement, latency bound p95/sub-Xms, concurrency, volume, throughput).
   - Calibrate claims to be defensible for a 2-3 year engineer (avoid claiming single-handed total ownership of entire enterprise platforms; prefer realistic module/service contributions).
7. PROFESSIONAL SUMMARY & POSITIONING COHERENCE:
   - Frame the candidate as a Backend Software Engineer with a solid enterprise Java/Spring Boot foundation, modern Python/FastAPI experience, and hands-on projects in event-driven architectures, cloud services, and AI systems.
   - Do NOT imply in the summary that payments/message-broker infrastructure were enterprise Cognizant responsibilities.
   - Organize the SKILLS section into logical categories, prominently featuring the technologies, frameworks, and tools requested in the job description.
8. LATEX STRUCTURE & MACRO INTEGRITY:
   - Preserve custom LaTeX macros exactly as defined in the template: \\resumeSep, \\resumeSubheading, \\resumeProject, \\resumeItemListStart, \\resumeItemListEnd, \\resumeHeadingContact.
   - Maintain pipe separators ($|$) where used in titles or headers.
9. TARGET LOCATION:
   - If a target job location (City, State) is specified, update the city/state in \\resumeHeadingContact accordingly.
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
            "COGNIZANT EXPERIENCE (.NET / C# TARGET STACK): Adapt Cognizant Technology Solutions to C#, .NET / ASP.NET Core, "
            "Entity Framework Core, SQL Server, and REST APIs."
        )
        usf_projects_instruction = (
            "USF & PROJECTS RULE (.NET): USF Graduate Researcher and Projects (SkillBeacon, AutoDocs, ByteRoute) MUST STAY Python "
            "(FastAPI, React, Lab Research, multi-agent workflows). Do NOT change USF or projects to .NET/C#."
        )
    elif target_stack == "java":
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (JAVA TARGET STACK): Cognizant Technology Solutions MUST be Java / Spring Boot, "
            "Microservices, REST APIs, and SQL/PostgreSQL."
        )
        usf_projects_instruction = (
            "USF & PROJECTS RULE (JAVA): USF Graduate Researcher and Projects MUST STAY Python "
            "(FastAPI, React, Lab Research, multi-agent workflows). Do NOT change USF or projects to Java."
        )
    elif target_stack == "node":
        cognizant_instruction = (
            "COGNIZANT EXPERIENCE (NODE.JS TARGET STACK): Cognizant Technology Solutions MUST remain Java / Spring Boot "
            "(do NOT change to Node.js)."
        )
        usf_projects_instruction = (
            "USF & PROJECTS (NODE.JS): Adapt USF Graduate Researcher and Projects to Node.js, TypeScript, React, "
            "Express/NestJS full-stack web platforms."
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

    prompt = f"""TARGET JOB DESCRIPTION:
{request.job_description}

TARGET ROLE NAME: {target_role}
TARGET LOCATION (CITY, STATE): {target_location}
TARGET INDUSTRY CONTEXT: {industry}
DETECTED PRIMARY STACK: {target_stack.upper()}
COMPANY CONTEXT: {company_context}
USER CONFIRMED SKILLS: {confirmed}
BANNED SKILLS (DO NOT INCLUDE): {banned}
EXTRA USER NOTES: {notes}

CRITICAL STACK & ROLE INSTRUCTIONS:
- CONTEXTUAL ATS CRITERIA AUDIT: Audit the base resume against the JD's specific criteria in context; strategically rewrite the existing bullets, projects, and skills to supply missing evidence and quantifiable metrics, elevating the resume to a 90%–95%+ pass rating.
- {cognizant_instruction}
- {usf_projects_instruction}
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
    target_stack = detect_target_stack(request.job_description, user_override=request.selected_stack_override)

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
