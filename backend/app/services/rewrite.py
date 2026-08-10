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
from .latex_projects import (
    force_replace_projects_section,
    projects_contain_ai_jargon,
    projects_section_was_replaced,
    replace_projects_section,
)
from .latex_skills import inject_canonical_skills_section, sanitize_skills_section
from .project_framing import (
    adapt_projects_to_job_description,
    build_evidence_linked_skills_instructions,
    build_project_reframing_instructions,
    build_selective_emphasis_instructions,
    build_stack_experience_framing_instructions,
    extract_jd_foundational_concepts,
    extract_resume_supported_terms,
    select_projects,
)
from .job_analyzer import detect_target_stack
from .skills_data import format_all_canonical_templates_for_prompt
from .rewrite_strategy import (
    build_rewrite_strategy,
    classify_target_role_identity,
    is_software_engineering_identity,
)

logger = logging.getLogger("uvicorn.error")


SYSTEM_PROMPT_BASE = """You are a resume rewriting assistant specialized in ATS-friendly LaTeX resumes.
Follow these rules:
- Return only complete LaTeX code, with no markdown fences.
- MANDATORY: DO NOT REMOVE any sections, job experiences, project entries, or education records. Every item in the original resume MUST be present in the rewrite.
- Preserve the candidate's identity, employers, dates, education, and template structure.
- Preserve existing separator characters exactly when they are part of the template, especially pipes like | between links, skills, dates, locations, or technologies.
- Do not convert pipe-separated content into commas, bullets, slashes, or prose unless the original template already uses that format.
- CRITICAL: Preserve the original LaTeX pipe separator style in skills lists. If the original uses '$|$', keep '$|$'. If it uses ' \\;|\\; ', keep ' \\;|\\; '. Do NOT mix separator styles or output malformed separators such as ' \\;|\\| '.
- Do not fabricate experience, metrics, credentials, or employment history.
- Rewrite bullets to match the target job language while keeping claims defensible.
- If you must prioritize, make the bullets for relevant roles more detailed, but NEVER delete older or less relevant experiences entirely.
- In transferable mode, mention target technologies as transferable when not directly supported.
- Treat C, C++, embedded, pointers, memory management, Kubernetes, and Terraform as high-risk direct substitutions.
- For high-risk substitutions, use transferable concept wording unless the skill is explicitly confirmed.
- Keep the resume ATS-friendly: no images, icons, tables, hidden text, or keyword stuffing.
- **MANDATORY**: Whenever possible, rewrite bullet points to follow the action-oriented X-Y-Z format: "Accomplished [X] as measured by [Y], by doing [Z]". Focus on quantifiable results, specific metrics, and the technical actions taken to achieve them.
- **MANDATORY BULLET STYLE** (shortlisted Microsoft/Tesla/Amazon-target resumes): Each experience and project bullet must follow this pattern:
  1. Start with a strong past-tense verb (Built, Designed, Engineered, Implemented, Optimized, Developed, Configured, Integrated, Automated).
  2. Weave 2–5 specific technologies inline (how), not only in a trailing skills list.
  3. Describe scope or scale (end-to-end, production-grade, high-volume, distributed, real-time, at scale) when defensible.
  4. End with a quantified outcome: % change, latency bound (p95/sub-Xms), uptime, throughput multiplier, or volume (10K+, 500k+, millions/day).
  Example shapes: "Designed end-to-end [pipelines/services] using [Tech A, B, C], reducing [metric] by X% and improving [throughput/latency/reliability]." / "Built [system] with [stack], enabling [capability] for N+ users/requests while holding p95 latency under Xms."
- Prefer dense, 1–2 sentence bullets (FAANG-style) over short generic lines. Avoid bullets with no number, scale, or bound.
- Avoid vague claims ("improved efficiency", "enhanced performance") without a metric. Show soft skills through technical evidence only.
- For projects: first bullet should establish end-to-end system scope and scale; follow with architecture, reliability/observability, and deployment bullets.
- Before returning the final LaTeX, perform an internal strict self-review against the job description, original resume, and rewrite rules.
- During that internal self-review, verify hard-skill coverage, required frameworks/tools, supported claims, LaTeX structure, pipe separators, dates, employers, role relevance ordering, and ATS readability.
- Do not output the self-review, notes, reasoning, markdown, JSON, or explanations. Output only the final corrected LaTeX after your internal review.

ROLE IDENTITY LOCK:
- Before rewriting, use the TARGET ROLE CLASSIFICATION block in the user prompt as the single dominant professional identity.
- Maintain that identity consistently across emphasized bullets, skills ordering, and project framing.
- Do NOT create mixed identities (e.g., "AI researcher + frontend engineer + DevOps architect") unless explicitly supported across the original resume.

ATS OPTIMIZATION:
- Prefer semantic alignment over exact keyword repetition.
- Never repeat the same technology excessively across multiple bullets.
- Do not insert technologies into bullets where they were not plausibly used.
- Prioritize strong technical accomplishments over keyword density.
- Preserve readability for human recruiters.

EVIDENCE-CONSTRAINED REWRITING:
- Only strengthen technologies directly supported elsewhere in the original resume.
- For adjacent but unconfirmed technologies, use transferable phrasing (e.g., "applied similar distributed systems principles...") — never imply production experience unless supported.

METRIC PRESERVATION:
- Preserve all existing quantified metrics whenever possible.
- Do NOT replace strong metrics with vague wording.
- Metrics for throughput, latency, uptime, concurrency, scale, test coverage, or transaction volume are HIGH PRIORITY and should usually be retained.

RELEVANCE PRIORITIZATION:
- Expand the most relevant experiences and projects first (see PRIORITY blocks in the user prompt).
- Less relevant experiences must remain present but may receive lighter rewrites.
- Preserve chronology and overall resume balance.

TECHNICAL DENSITY:
- Integrate technologies into the accomplishment narrative; avoid isolated trailing technology dumps.
- Prefer: "Built distributed REST APIs using Java, Spring Boot, Redis, and PostgreSQL..."
- Over: "Built APIs. Technologies used: Java, Spring Boot, Redis."

WEAK BULLET ELIMINATION:
- Do not leave generic bullets lacking technical detail, measurable impact, production scope, or scale.
- Replace weak phrasing such as "Worked on backend services" or "Improved system performance" with specific, metric-backed implementations when supported by the source resume.

PRODUCTION ENGINEERING VOICE (software engineering identities):
- Avoid academic or research-heavy phrasing: "investigated", "studied", "explored", "researched" unless the source bullet is explicitly research-only.
- Prefer: built, designed, implemented, optimized, deployed, scaled, engineered.

"""

SYSTEM_PROMPT_TITLE_ALIGNMENT = """
TITLE ALIGNMENT MODE IS ENABLED. Additional rules:
- You MAY adjust the candidate's job titles in the LaTeX to better align with the target role name provided, but ONLY within these strict boundaries:
  1. The new title must be a genuine synonym or a level-appropriate variant of the original title (e.g. "Software Developer" -> "Software Engineer", "Jr. Developer" -> "Junior Software Engineer", "Backend Developer" -> "Backend Engineer").
  2. Do NOT change a title to a completely different discipline (e.g. do NOT change "Frontend Developer" to "DevOps Engineer" or "Data Scientist").
  3. Do NOT inflate seniority beyond what is defensible (e.g. do NOT change "Junior Developer" to "Senior Engineer" or "Lead").
  4. Do NOT invent titles that were never held (e.g. do NOT add "Manager" or "Architect" if there is no leadership evidence in the resume).
  5. Apply the same title change consistently to all occurrences of that title in the LaTeX.
  6. If the original title is already a close match to the target role, leave it unchanged.
- After adjusting titles, continue with all other rewrite rules as normal.
"""


def build_system_prompt(align_titles: bool) -> str:
    if align_titles:
        return SYSTEM_PROMPT_BASE.rstrip() + "\n" + SYSTEM_PROMPT_TITLE_ALIGNMENT
    return SYSTEM_PROMPT_BASE



def get_effective_industry(selected_industry: str | None, job_description: str, resume_text: str = "", company_context: str | None = None) -> str:
    from .job_analyzer import resolve_industry

    industry, _, _ = resolve_industry(
        job_description,
        company_context,
        user_selected=selected_industry,
    )
    return industry


def get_effective_role_category(selected_role_category: str | None, job_description: str) -> str:
    if selected_role_category and selected_role_category.strip():
        return selected_role_category.strip()
    
    from .job_analyzer import detect_details_with_keywords
    _, detected = detect_details_with_keywords(job_description)
    return detected or "Software Engineer"


def build_user_prompt(
    request: RewriteRequest,
    current_score: float,
    missing_terms: list[str],
    unsupported_terms: list[str],
    effective_industry: str,
    effective_role_category: str,
    selected_projects: list[dict],
    rewrite_strategy_block: str,
    target_role_identity: str,
    foundational_concepts: list[str],
    evidence_skills_block: str,
    reframing_block: str,
    selective_emphasis_block: str,
) -> str:
    confirmed = ", ".join(request.confirmed_skills) or "None provided"
    banned = ", ".join(request.banned_skills) or "None provided"
    company_context = request.company_context or "None provided"
    notes = request.extra_user_notes or "None provided"
    high_risk = ", ".join(sorted(HIGH_RISK_DIRECT_SUBSTITUTIONS))
    target_role = request.role_name or "Not specified"
    title_instruction = (
        f"Title alignment is ENABLED. Align job titles toward the target role: '{target_role}' "
        "following the title alignment rules in the system prompt."
        if request.align_titles
        else "Title alignment is DISABLED. Do NOT change any job titles."
    )
    
    proj_a, proj_b = selected_projects[0], selected_projects[1]
    bullets_a = "\n".join([f"- {b}" for b in proj_a["bullets"]])
    bullets_b = "\n".join([f"- {b}" for b in proj_b["bullets"]])
    
    foundational_block = ""
    if foundational_concepts:
        foundational_block = (
            "JD FOUNDATIONAL CONCEPTS (surface naturally in experience bullets when supported by resume):\n"
            + ", ".join(foundational_concepts)
            + "\nExample: 'Implemented Java validation services using OOP abstractions and exception-handling patterns...'\n"
        )

    target_stack = detect_target_stack(request.job_description, user_override=request.selected_stack_override)
    stack_block = build_stack_experience_framing_instructions(target_stack)

    project_instructions = f"""
TARGET ROLE CATEGORY: {effective_role_category}
TARGET COMPANY INDUSTRY: {effective_industry}
TARGET DETECTED STACK: {target_stack.upper()}

{stack_block}

{reframing_block}

{selective_emphasis_block}

{foundational_block}

{format_all_canonical_templates_for_prompt()}

{evidence_skills_block}

MANDATORY PROJECTS TO INSERT/REPLACE:
You MUST replace the projects in the resume with the following two project templates, customized for the target industry '{effective_industry}'.

Project 1:
- Role-framed Title (USE THIS): {proj_a["title"]}
- Core Tech Stack: {", ".join(proj_a["tech_stack"])}
- Core Bullets to Adapt:
{bullets_a}

Project 2:
- Role-framed Title (USE THIS): {proj_b["title"]}
- Core Tech Stack: {", ".join(proj_b["tech_stack"])}
- Core Bullets to Adapt:
{bullets_b}

PROJECT INSERTION RULES:
1. The PROJECTS section content is injected programmatically after rewrite — focus on Experience, Skills, and bullet quality.
2. If you modify projects anyway, use ONLY Project 1 and Project 2 below with the exact role-framed titles.
2. Adapt these two projects to the target industry '{effective_industry}' AND identity '{target_role_identity}'. Use the role-framed titles above — do not revert to AI-centric naming for backend/fullstack identities. Customize domain terms and metrics for {effective_industry}. Keep listed tech stacks unless evidence-linked skills rules forbid a vendor. Use 2–3 bullets per project for backend/fullstack identities (compress); 3–4 for AI/ML identities. Preserve template metrics when defensible. For USF/research experience: prefer 'backend services supporting AI-assisted workflows for 60+ concurrent users with sub-2s latency' over '20B-parameter LLM' unless the original resume explicitly includes that scale claim.
3. Keep the resume template formatting (margins, fonts, structural commands) exactly as in the original LaTeX.
4. Update the 'Skills' or 'Technical Skills' section following EVIDENCE-LINKED SKILLS rules above. Only add missing JD terms when supported or clearly transferable. Reorder skills so the top lines match '{target_role_identity}' priorities.
   - Ensure specific editors, IDEs, or assistant tools mentioned in the job description (such as 'Cursor', 'Claude Code', or 'Copilot') are explicitly added to the skills list if they are mentioned as requirements or preferences.
   - Avoid dumping irrelevant skill names that have no relation to the job requirements.
5. Limit the technologies listed in each project's tech stack to the top 4 to 6 most critical and relevant technologies only.
6. PROJECT HEADER LAYOUT: Preserve the original resume's project header macro when present.
   - If the source uses \\resumeProjectHeading{{Title}} (title only), keep that pattern.
   - Otherwise use a TWO-LINE tabular block (bold title, then \\small\\textit{{tech stack}}).
   Do NOT put the project name and tech stack on one line separated by & when the title is long.

SECTION ORDER RULE:
The sections in the output LaTeX MUST follow this exact order:
1. Header (name, contact)
2. Technical Skills
3. Experience
4. Projects
5. Education
If the original resume places Education before Projects, move it to after Projects in the rewritten output.

WORK EXPERIENCE WRITING RULES:
1. You MUST NOT change the candidate's actual job duties, employers, titles, or dates (do not fabricate experience).
2. Adapt the work experience bullets to showcase matching technical skills and keywords from the job description while keeping the candidate's original responsibilities and contexts intact.
3. Rewrite every experience bullet using the MANDATORY BULLET STYLE: action verb + inline tech + scope + quantified outcome. Preserve or adapt defensible metrics from the original resume; do not invent employers or roles.
4. When the job emphasizes cloud, data, or distributed systems, use ownership phrasing where accurate (e.g., "end-to-end", "production-grade", "at scale", "from ingestion to deployment") without claiming work the candidate did not do.
5. Match target-company tone when inferable from the job description: Microsoft/Azure roles favor cloud-native, reliability, and observability language; data-engineering roles favor pipeline, ETL/ELT, and data-modeling terms; infra/platform roles favor CI/CD, Kubernetes, and SLO/uptime metrics.
"""

    swe_voice = ""
    if is_software_engineering_identity(target_role_identity):
        swe_voice = (
            "\nSOFTWARE ENGINEERING VOICE: Use production-oriented verbs "
            "(built, designed, implemented, optimized, deployed, scaled, engineered). "
            "Avoid academic phrasing unless the source bullet is explicitly research-only.\n"
        )

    return f"""
{rewrite_strategy_block}
{swe_voice}
Rewrite mode: {request.rewrite_mode}
Target keyword threshold: {request.target_match_threshold}%
Current heuristic score: {current_score}%
Target role name: {target_role}
Title alignment instruction: {title_instruction}
Confirmed skills: {confirmed}
Banned skills: {banned}
High-risk direct substitutions: {high_risk}
Missing target terms: {", ".join(missing_terms) or "None"}
Unsupported/high-risk terms: {", ".join(unsupported_terms) or "None"}

{project_instructions}

Company/research context:
{company_context}

User notes:
{notes}

Job description:
{request.job_description}

Original LaTeX resume:
{request.resume_latex}

Task:
Generate one final improved ATS-friendly LaTeX resume. Keep the existing LaTeX template as much as possible.
If the job wants a stack adjacent to the candidate's actual stack, translate the experience through defensible concepts.
If the job wants C/C++ and the resume shows Python/Java only, emphasize OOP, algorithms, data structures, performance, concurrency, and systems concepts, but do not claim direct C/C++ work unless C/C++ is confirmed.
Prioritize hard skills, frameworks, tools, databases, cloud/devops, domain terms, and core responsibilities over generic soft skills such as analytical, communicator, team player, or detail-oriented.
EXPERIENCE REORDERING RULE: Evaluate every work experience entry against the job description. If a later experience (e.g. the second or third job) is substantially more relevant to the target role than the one currently listed first, you MUST reorder them so the most relevant experience appears first in the Experience section. Move the entire experience block (heading + bullets) — do not split or merge entries. Dates must remain accurate and visible next to each role. If relevance is roughly equal, preserve the original chronological order.
Before finalizing, internally audit the rewritten resume using this checklist:
1. Required hard skills and frameworks are represented when supported or defensibly transferable.
2. Unsupported/high-risk skills are not claimed directly unless confirmed.
3. Soft skills are shown through concrete technical evidence, not generic phrases.
4. LaTeX commands, braces, custom macros, layout, and section structure are preserved.
5. Pipe separators | are preserved where they existed in the original template.
6. Employers, dates, education, project names, and contact/header structure are not fabricated.
7. The result is readable by ATS and humans without keyword stuffing.
Return only the final corrected LaTeX. Do not return the audit checklist or explanation.
"""


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
        "temperature": 1,
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
        kwargs["extra_body"] = {
            "reasoning": {
                "enabled": True
            }
        }
    completion = client.chat.completions.create(**kwargs)
    if completion.choices and len(completion.choices) > 0:
        print(f"DEBUG: OpenAI/OpenRouter finish reason: {completion.choices[0].finish_reason}", flush=True)
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
        print(f"DEBUG: Gemini finish reason: {response.candidates[0].finish_reason}", flush=True)
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
    if latex.strip().endswith(r"\end{document}"):
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

    effective_industry = get_effective_industry(request.selected_industry, request.job_description, resume_text, request.company_context)
    effective_role_category = get_effective_role_category(request.selected_role_category, request.job_description)
    target_stack = detect_target_stack(request.job_description, user_override=request.selected_stack_override)

    missing_terms = [kw.term for kw in initial_score.missing_keywords]
    unsupported_terms = [kw.term for kw in initial_score.unsupported_keywords]

    target_identity = classify_target_role_identity(
        request.job_description, resume_text, effective_role_category
    )
    selected_projects = select_projects(
        effective_role_category, request.job_description, target_identity
    )
    selected_projects = adapt_projects_to_job_description(
        selected_projects,
        request.job_description,
        effective_industry,
        target_identity,
    )

    strategy = build_rewrite_strategy(
        request.job_description,
        request.resume_latex,
        effective_role_category,
        selected_projects,
        missing_terms=missing_terms,
    )
    strategy_block = strategy.to_prompt_block()

    foundational = extract_jd_foundational_concepts(request.job_description)
    supported = extract_resume_supported_terms(resume_text)
    evidence_block = build_evidence_linked_skills_instructions(
        supported, missing_terms, request.confirmed_skills
    )
    reframing_block = build_project_reframing_instructions(target_identity)
    emphasis_block = build_selective_emphasis_instructions(
        target_identity, strategy.priority_experiences
    )

    prompt = build_user_prompt(
        request,
        initial_score.match_score,
        missing_terms,
        unsupported_terms,
        effective_industry,
        effective_role_category,
        selected_projects,
        strategy_block,
        target_identity,
        foundational,
        evidence_block,
        reframing_block,
        emphasis_block,
    )
    res = generate_rewrite(prompt, request.align_titles)
    generated_text = res[0]
    provider = res[1]
    provider_err = res[2] if len(res) > 2 else None

    if generated_text:
        print(f"DEBUG: Generated text length: {len(generated_text)}", flush=True)
        print(f"DEBUG: Generated text ends with '\\end{{document}}': {generated_text.strip().endswith('\\end{document}')}", flush=True)
        print(f"DEBUG: Last 150 characters of generated text:\n{generated_text[-150:]}", flush=True)
    else:
        print("DEBUG: Generated text is None or empty!", flush=True)

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
    # Strip markdown fences if AI ignores instructions
    if rewritten.startswith("```"):
        # Remove first line (fences) and last line (fences)
        lines = rewritten.splitlines()
        if len(lines) >= 2:
            # Check if first line has a language tag like ```latex
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Check if last line is ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            rewritten = "\n".join(lines).strip()

    rewritten = repair_truncated_latex(rewritten)

    post_warnings: list[str] = []
    project_injection_applied = False
    final_project_guard_applied = False
    skills_sanitized = False

    if selected_projects:
        pre_inject = rewritten
        if is_software_engineering_identity(target_identity):
            # SWE identities: always swap PROJECTS deterministically; never trust LLM project picks.
            rewritten = force_replace_projects_section(
                rewritten,
                selected_projects,
                request.resume_latex,
                target_identity,
            )
        else:
            injected = replace_projects_section(
                rewritten,
                selected_projects,
                request.resume_latex,
                target_identity,
            )
            if injected != rewritten:
                rewritten = injected

            needs_force = (
                not projects_section_was_replaced(request.resume_latex, rewritten, selected_projects)
                or projects_contain_ai_jargon(rewritten)
            )
            if needs_force:
                rewritten = force_replace_projects_section(
                    rewritten,
                    selected_projects,
                    request.resume_latex,
                    target_identity,
                )

        project_injection_applied = rewritten != pre_inject and projects_section_was_replaced(
            request.resume_latex, rewritten, selected_projects
        )
        if is_software_engineering_identity(target_identity) and projects_contain_ai_jargon(rewritten):
            post_warnings.append(
                "AI-centric project titles still detected after injection; verify the PROJECTS section header and list macros in the template."
            )
        elif not project_injection_applied:
            post_warnings.append(
                "Projects section could not be programmatically replaced; verify PROJECTS section macros match the template."
            )

    pre_skills = rewritten
    supported = extract_resume_supported_terms(latex_to_text(request.resume_latex))
    rewritten = inject_canonical_skills_section(
        rewritten,
        target_stack,
        job_description=request.job_description,
        banned_skills=request.banned_skills,
        original_latex=request.resume_latex,
    )
    rewritten = sanitize_skills_section(
        rewritten,
        supported,
        request.confirmed_skills,
        target_identity,
        request.resume_latex,
        banned_skills=request.banned_skills,
    )
    skills_sanitized = rewritten != pre_skills

    if (
        selected_projects
        and is_software_engineering_identity(target_identity)
        and projects_contain_ai_jargon(rewritten)
    ):
        pre_guard = rewritten
        rewritten = force_replace_projects_section(
            rewritten,
            selected_projects,
            request.resume_latex,
            target_identity,
        )
        final_project_guard_applied = rewritten != pre_guard
        if projects_contain_ai_jargon(rewritten):
            post_warnings.append(
                "Backend project guard still detected AI-project jargon after final replacement; inspect the PROJECTS section manually."
            )

    final_text = latex_to_text(rewritten)
    final_score = score_keywords(
        job_keywords,
        final_text,
        target_threshold=request.target_match_threshold,
        rewrite_mode=request.rewrite_mode,
        confirmed_skills=request.confirmed_skills,
    )
    warnings = list(final_score.warnings) + post_warnings
    original_pipe_count = request.resume_latex.count("|")
    rewritten_pipe_count = rewritten.count("|")
    if original_pipe_count and rewritten_pipe_count < original_pipe_count:
        warnings.append(
            f"The rewrite reduced pipe separators from {original_pipe_count} to {rewritten_pipe_count}. Review template separators before using the output."
        )

    changes = [
        "Post-process pipeline v3 active (deterministic project injection for SWE roles).",
        f"Rewrote resume bullets and skills toward the target job description using {provider}.",
        "Applied the selected rewrite mode and high-risk substitution guardrails.",
        f"Selected projects based on role category '{effective_role_category}' and industry '{effective_industry}'.",
        f"Target role identity: {target_identity}; selected project IDs {[p['id'] for p in selected_projects]} ({selected_projects[0].get('applied_framing', target_identity)} framing).",
        f"Top skills: {', '.join(strategy.top_skills[:5]) or 'inferred'}.",
    ]
    if project_injection_applied:
        changes.append(
            f"Injected projects {[p['id'] for p in selected_projects]}: "
            f"\"{selected_projects[0]['title'][:50]}...\" and "
            f"\"{selected_projects[1]['title'][:50]}...\" (deterministic LaTeX replacement)."
        )
    elif selected_projects:
        changes.append(
            "Project injection attempted but did not modify output — check PROJECTS section in template."
        )
    if skills_sanitized:
        changes.append("Sanitized TECHNICAL SKILLS / SKILLS section (removed unsupported vendors/tools).")
    if final_project_guard_applied:
        changes.append("Applied final backend project guard to remove stale AI/agent project output.")
    changes.extend([
        f"Adapted project bullets for '{effective_industry}' industry and '{target_identity}' identity.",
        f"Heuristic keyword score changed from {initial_score.match_score}% to {final_score.match_score}%.",
    ])
    if request.align_titles:
        changes.append(
            f"Title alignment was ENABLED: job titles may have been adjusted toward '{request.role_name or 'target role'}' "
            "using synonym/level-appropriate substitutions only."
        )
    return RewriteResponse(
        rewritten_latex=rewritten,
        match_score=final_score.match_score,
        target_met=final_score.target_met,
        matched_keywords=final_score.matched_keywords,
        missing_keywords=final_score.missing_keywords,
        unsupported_keywords=final_score.unsupported_keywords,
        warnings=warnings,
        changes_made=changes,
    )
