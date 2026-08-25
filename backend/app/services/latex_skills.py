"""Post-process skills section to remove unsupported/hallucinated terms."""

from __future__ import annotations

import re

from .skills_data import get_skills_template_for_stack

# Terms that must not appear unless in resume-supported set or confirmed skills
RESTRICTED_SKILL_TERMS = (
    "oracle",
    "langgraph",
    "hibernate",
    "kafka",
    "jsp",
    "servlet",
    "spring security",
    "mysql",
)

AI_SKILL_TERMS = (
    "langgraph",
    "langchain",
    "prompt engineering",
    "llm integration",
)


def _strip_term_from_parenthetical(text: str, term: str) -> str:
    """Remove term from parenthetical lists, e.g. SQL (Oracle, PostgreSQL) -> SQL (PostgreSQL)."""

    def _clean_paren(match: re.Match[str]) -> str:
        inner = match.group(1)
        parts = [p.strip() for p in re.split(r",\s*", inner) if p.strip()]
        kept = [p for p in parts if term.lower() not in p.lower()]
        if not kept:
            return ""
        if len(kept) == 1 and len(parts) == 1:
            return kept[0]
        return f"({', '.join(kept)})"

    updated = re.sub(
        rf"\(([^)]*\b{re.escape(term)}\b[^)]*)\)",
        _clean_paren,
        text,
        flags=re.IGNORECASE,
    )
    # Drop empty parens left after removing the only parenthetical item
    updated = re.sub(r"\(\s*\)", "", updated)
    updated = re.sub(r"\s{2,}", " ", updated)
    return updated


def _preferred_pipe_separator(original_latex: str) -> str:
    """Prefer the separator style already used by the original skills section."""
    original_skills = _extract_skills_section(original_latex)
    if "$|$" in original_skills:
        return " $|$ "
    if r"\;|\;" in original_skills or r"\;|" in original_skills:
        return r" \;|\; "
    return " $|$ "


def _normalize_skill_separators(text: str, preferred_separator: str = r" \;|\; ") -> str:
    """Normalize LaTeX pipe separators after model output or term removal."""
    updated = re.sub(r"\\;\s*\|\s*\\\|\s*", preferred_separator, text)
    updated = re.sub(r"\\;\s*\|\s*\\;\s*", preferred_separator, updated)
    updated = re.sub(r"\s*\$\|\$\s*", preferred_separator, updated)
    updated = re.sub(r"(\s*" + re.escape(preferred_separator.strip()) + r"\s*){2,}", preferred_separator, updated)
    updated = re.sub(re.escape(preferred_separator.strip()) + r"\s*\\\[", r"\\\\[", updated)
    updated = re.sub(r"\s{2,}", " ", updated)
    return updated


def _extract_skills_section(latex: str) -> str:
    section_match = re.search(
        r"\\section\{(?:TECHNICAL )?SKILLS\}(.*?)(?=\\section\{|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return section_match.group(1).lower() if section_match else ""


def _remove_skill_term(text: str, term: str, preferred_separator: str = r" \;|\; ") -> str:
    """Remove a single skill term across pipe-separated, comma-separated, and plain skill lines."""
    escaped = re.escape(term)
    updated = _strip_term_from_parenthetical(text, term)
    patterns = [
        rf"\s*\\;\|\s*\b{escaped}\b",
        rf"\b{escaped}\b\s*\\;\|\s*",
        rf"\s*\$\|\$\s*\b{escaped}\b",
        rf"\b{escaped}\b\s*\$\|\$\s*",
        rf",\s*\b{escaped}\b",
        rf"\b{escaped}\b,\s*",
        rf"\s+\b{escaped}\b(?=\s|\\\\|\}})",
    ]
    for pattern in patterns:
        updated = re.sub(pattern, "", updated, flags=re.IGNORECASE)
    return _normalize_skill_separators(updated, preferred_separator)


def sanitize_skills_section(
    latex: str,
    supported_terms: set[str],
    confirmed_skills: list[str],
    target_role_identity: str,
    original_latex: str,
    banned_skills: list[str] | None = None,
) -> str:
    """
    Remove skill terms from TECHNICAL SKILLS / SKILLS that were not in the original resume
    unless user confirmed them, or if listed in banned_skills.
    """
    preferred_separator = _preferred_pipe_separator(original_latex)
    allowed = {t.lower() for t in supported_terms}
    allowed.update(t.lower() for t in confirmed_skills)
    role_forbidden = set()
    if target_role_identity in ("backend_engineer",):
        role_forbidden.update(AI_SKILL_TERMS)

    # Terms present in the original skills block are allowed for the same identity,
    # but terms appearing only in old project bullets should not protect hallucinated skills.
    orig_lower = _extract_skills_section(original_latex)
    for term in RESTRICTED_SKILL_TERMS:
        if term.lower() in role_forbidden:
            continue
        if re.search(rf"\b{re.escape(term)}\b", orig_lower):
            allowed.add(term)

    def may_keep(term: str) -> bool:
        t = term.lower().strip()
        if not t:
            return True
        if t in role_forbidden:
            return False
        for a in allowed:
            if a in t or t in a:
                return True
        return False

    section_match = re.search(
        r"(\\section\{(?:TECHNICAL )?SKILLS\}.*?)(?=\\section\{|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not section_match:
        return latex

    section = section_match.group(1)
    updated = section

    for term in RESTRICTED_SKILL_TERMS:
        if may_keep(term):
            continue
        if not re.search(rf"\b{re.escape(term)}\b", updated, re.IGNORECASE):
            continue
        updated = _remove_skill_term(updated, term, preferred_separator)

    if target_role_identity in ("backend_engineer", "fullstack_engineer"):
        for term in AI_SKILL_TERMS:
            if may_keep(term):
                continue
            updated = _remove_skill_term(updated, term, preferred_separator)
            updated = re.sub(
                rf"\\textbf\{{AI \& Observability:\}}\s*[^\\]*\\?\[1pt\]\s*",
                "",
                updated,
                flags=re.IGNORECASE,
            )

    if banned_skills:
        for b_term in banned_skills:
            if b_term.strip():
                updated = _remove_skill_term(updated, b_term.strip(), preferred_separator)

    # Strip verbose HR qualification sentences accidentally included in skills
    updated = re.sub(
        r"(?:\\;\|\s*|\$\|\$\s*|,?\s*)Experience with [^\\\n\r}]+",
        "",
        updated,
        flags=re.IGNORECASE,
    )

    updated = _normalize_skill_separators(updated, preferred_separator)

    if updated != section:
        latex = latex[: section_match.start(1)] + updated + latex[section_match.end(1) :]
    return latex


def inject_canonical_skills_section(
    latex: str,
    target_stack: str,
    job_description: str = "",
    banned_skills: list[str] | None = None,
    original_latex: str = "",
) -> str:
    """
    Injects or replaces the SKILLS section using the canonical template for the target stack (java, ai, python, node).
    Filters out any banned skills if provided.
    """
    tmpl = get_skills_template_for_stack(target_stack)
    if not tmpl or "raw_latex" not in tmpl:
        return latex

    raw = tmpl["raw_latex"]
    if banned_skills:
        preferred_sep = _preferred_pipe_separator(original_latex) if original_latex else r" \;|\; "
        for b_term in banned_skills:
            if b_term.strip():
                raw = _remove_skill_term(raw, b_term.strip(), preferred_sep)

    # Check if there is an existing SKILLS section in the document to replace
    section_match = re.search(
        r"\\section\{(?:TECHNICAL )?SKILLS\}.*?(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if section_match:
        return latex[: section_match.start()] + raw + "\n\n" + latex[section_match.end() :]

    # If no SKILLS section exists, insert before Experience or Education
    insertion_points = [
        r"\\section\{EXPERIENCE\}",
        r"\\section\{EDUCATION\}",
        r"\\end\{document\}",
    ]
    for pattern in insertion_points:
        match = re.search(pattern, latex, flags=re.IGNORECASE)
        if match:
            return latex[: match.start()] + raw + "\n\n" + latex[match.start() :]

    return latex.rstrip() + "\n\n" + raw


def reorder_experience_for_java(latex: str) -> str:
    """Ensure Cognizant Technology Solutions appears before USF in EXPERIENCE for Java roles."""
    exp_match = re.search(
        r"(\\section\{EXPERIENCE\}.*?)(?=\\section\{|\\end\{document\}|\Z)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not exp_match:
        return latex

    exp_block = exp_match.group(1)
    cog_match = re.search(
        r"\\resumeSubheading\s*\{[^}]*Cognizant.*?(?=\\resumeSubheading|\\end\{itemize\}|\Z)",
        exp_block,
        flags=re.DOTALL | re.IGNORECASE,
    )
    usf_match = re.search(
        r"\\resumeSubheading\s*\{[^}]*University of South Florida.*?(?=\\resumeSubheading|\\end\{itemize\}|\Z)",
        exp_block,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if cog_match and usf_match and cog_match.start() > usf_match.start():
        cog_text = cog_match.group(0).strip()
        usf_text = usf_match.group(0).strip()

        new_exp_block = (
            exp_block[: usf_match.start()]
            + cog_text
            + "\n\n  "
            + usf_text
            + exp_block[cog_match.end() :]
        )
        latex = latex[: exp_match.start(1)] + new_exp_block + latex[exp_match.end(1) :]

    return latex
