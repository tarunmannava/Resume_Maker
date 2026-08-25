"""Deterministic PROJECTS section injection into resume LaTeX."""

from __future__ import annotations

import re


def _escape_latex_text(text: str) -> str:
    """Escape characters that break LaTeX resumeItem arguments."""
    t = text.replace("\\", "\\textbackslash{}")
    t = t.replace("&", "\\&")
    t = t.replace("%", "\\%")
    t = t.replace("#", "\\#")
    t = t.replace("_", "\\_")
    return t


def _format_bullet(bullet: str) -> str:
    """Preserve existing \\textbf{} markup; escape the rest."""
    if "\\textbf{" in bullet:
        return bullet.replace("%", "\\%")
    return _escape_latex_text(bullet)


def _tech_stack_line(project: dict, max_items: int = 6) -> str:
    return ", ".join(project.get("tech_stack", [])[:max_items])


def _uses_two_arg_project_macro(original_latex: str) -> bool:
    return bool(re.search(r"\\newcommand\{\\resumeProject\}\[2\]", original_latex))


def build_single_project_block(
    project: dict,
    original_latex: str,
    target_role_identity: str,
) -> str:
    title = _escape_latex_text(project["title"])
    stack = _escape_latex_text(_tech_stack_line(project))
    bullets = project.get("bullets", [])

    lines: list[str] = []

    # Prefer two-arg \\resumeProject when the template defines it (title + tech stack line)
    if _uses_two_arg_project_macro(original_latex):
        lines.append(f"  \\resumeProject{{{title}}}{{{stack}}}")
    elif r"\resumeProjectHeading" in original_latex:
        lines.append(f"  \\resumeProjectHeading{{{title}}}")
    elif r"\resumeProject{" in original_latex:
        lines.append(f"  \\resumeProject{{{title}}}{{{stack}}}")
    else:
        lines.extend([
            "  \\vspace{-2pt}\\item[]",
            "  \\begin{tabular*}{0.97\\textwidth}[t]{l}",
            f"    \\textbf{{{title}}} \\\\",
            f"    \\small\\textit{{{stack}}}",
            "  \\end{tabular*}\\vspace{-7pt}",
        ])

    lines.append("  \\resumeItemListStart")
    for bullet in bullets:
        lines.append(f"    \\resumeItem{{{_format_bullet(bullet)}}}")
    lines.append("  \\resumeItemListEnd")
    lines.append("")

    return "\n".join(lines)


def build_projects_section_body(
    projects: list[dict],
    original_latex: str,
    target_role_identity: str,
) -> str:
    blocks = [
        build_single_project_block(p, original_latex, target_role_identity)
        for p in projects[:2]
    ]
    return "\n".join(blocks)


def build_projects_section(
    projects: list[dict],
    original_latex: str,
    target_role_identity: str,
) -> str:
    body = build_projects_section_body(projects, original_latex, target_role_identity)
    return (
        "\\section{PROJECTS}\n"
        "\\resumeSubHeadingListStart\n\n"
        f"{body}\n"
        "\\resumeSubHeadingListEnd\n\n"
    )


def insert_projects_section(
    latex: str,
    projects: list[dict],
    original_latex: str,
    target_role_identity: str,
) -> str:
    """Add a PROJECTS section when the source resume does not already have one."""
    section = build_projects_section(projects, original_latex, target_role_identity)
    insertion_points = [
        r"\\section\{EDUCATION\}",
        r"\\section\{(?:SKILLS|TECHNICAL SKILLS)\}",
        r"\\section\{CERTIFICATIONS\}",
        r"\\end\{document\}",
    ]

    for pattern in insertion_points:
        match = re.search(pattern, latex, flags=re.IGNORECASE)
        if match:
            return latex[: match.start()] + section + latex[match.start() :]

    return latex.rstrip() + "\n\n" + section


def force_replace_projects_section(
    latex: str,
    projects: list[dict],
    original_latex: str,
    target_role_identity: str,
) -> str:
    """
    Replace everything from \\section{PROJECTS} up to the next \\section{...}.
    Used when the LLM emits \\resumeProject blocks the softer regex misses.
    """
    replacement = build_projects_section(projects, original_latex, target_role_identity)
    pattern = (
        r"\\section\{(?:PROJECTS|Technical Projects)\}"
        r".*?"
        r"(?=\\section\{)"
    )
    matches = list(re.finditer(pattern, latex, flags=re.DOTALL | re.IGNORECASE))
    if matches:
        pieces: list[str] = []
        last_end = 0
        for index, match in enumerate(matches):
            pieces.append(latex[last_end : match.start()])
            if index == 0:
                pieces.append(replacement)
            last_end = match.end()
        pieces.append(latex[last_end:])
        return "".join(pieces)
    return insert_projects_section(latex, projects, original_latex, target_role_identity)


def replace_projects_section(
    latex: str,
    projects: list[dict],
    original_latex: str,
    target_role_identity: str,
) -> str:
    """
    Replace the contents of the PROJECTS section with the selected project templates.
    Preserves section header and list start/end macros from the rewritten document.
    """
    body = build_projects_section_body(projects, original_latex, target_role_identity)

    patterns = [
        (
            r"(\\section\{(?:PROJECTS|Technical Projects)\}\s*"
            r"(?:%[^\n]*\n\s*)*\\resumeSubHeadingListStart\s*)"
            r"(.*?)"
            r"(\s*\\resumeSubHeadingListEnd)"
        ),
        (
            r"(\\section\{(?:PROJECTS|Technical Projects)\}\s*"
            r"(?:%[^\n]*\n\s*)*)"
            r"(.*?)"
            r"(\s*\\section\{(?:EDUCATION|TECHNICAL SKILLS|SKILLS|CERTIFICATIONS)\})"
        ),
    ]

    for pattern in patterns:
        match = re.search(pattern, latex, flags=re.DOTALL | re.IGNORECASE)
        if match and len(match.groups()) == 3:
            return latex[: match.start(2)] + "\n" + body + "\n" + latex[match.end(2) :]

    return force_replace_projects_section(latex, projects, original_latex, target_role_identity)


def projects_contain_ai_jargon(latex: str) -> bool:
    lower = latex.lower()
    markers = (
        "langgraph",
        "multi-agent",
        "prompt registry",
        "prompt experimentation",
        "token tracing",
        "autonomous multi-agent",
    )
    projects_matches = re.finditer(
        r"\\section\{(?:PROJECTS|Technical Projects)\}(.*?)\\section\{",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return any(
        marker in projects_match.group(1).lower()
        for projects_match in projects_matches
        for marker in markers
    )


def projects_section_was_replaced(original: str, rewritten: str, projects: list[dict]) -> bool:
    """Check if at least one selected project title appears in the rewritten output."""
    if not projects:
        return False
    title_fragment = projects[0]["title"][:30].lower()
    return title_fragment in rewritten.lower()


def cap_projects_at_max(latex: str, max_projects: int = 2) -> str:
    """Cap number of projects in PROJECTS section to max_projects (default 2)."""
    section_match = re.search(
        r"(\\section\{(?:PROJECTS|Technical Projects)\}\s*"
        r"(?:%[^\n]*\n\s*)*\\resumeSubHeadingListStart\s*)"
        r"(.*?)"
        r"(\s*\\resumeSubHeadingListEnd)",
        latex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not section_match:
        return latex

    header = section_match.group(1)
    body = section_match.group(2)
    footer = section_match.group(3)

    proj_starts = list(re.finditer(r"(\\resumeProject(?:Heading)?\{|\\item\b)", body))
    if len(proj_starts) <= max_projects:
        return latex

    cutoff_idx = proj_starts[max_projects].start()
    trimmed_body = body[:cutoff_idx].rstrip()
    return latex[: section_match.start(0)] + header + "\n" + trimmed_body + "\n" + footer + latex[section_match.end(0) :]
