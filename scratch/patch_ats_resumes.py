"""Apply ATS-friendly formatting fixes to scratch resume .tex files."""

from __future__ import annotations

import re
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent

MACRO_BLOCK = r"""
\newcommand{\resumeItem}[1]{
  \item\small{#1}
}

\input{ats_macros.tex}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
""".strip()

HEADER_OLD = re.compile(
    r"Tampa, FL.*?\\href\{https://github\.com/tarunmannava\}\{GitHub\}",
    re.DOTALL,
)
HEADER_NEW = "\\resumeHeadingContact"

SKILLS_PIPE = re.compile(r"\$\|\$")


def _replace_macros(tex: str) -> str:
    match = re.search(
        r"\\newcommand\{\\resumeSubheading\}.*?"
        r"(?=\\newcommand\{\\resumeSubHeadingListStart\}|\\begin\{document\})",
        tex,
        flags=re.DOTALL,
    )
    if not match:
        return tex
    tex = tex[: match.start()] + MACRO_BLOCK + "\n\n" + tex[match.end() :]
    tex = re.sub(r"\\newcommand\{\\resumeProjectHeading\}.*?\n", "", tex)
    tex = re.sub(r"\\newcommand\{\\resumeProject\}.*?\n", "", tex)
    return tex


def _comma_skills(tex: str) -> str:
    section = re.search(
        r"(\\section\{(?:SKILLS|TECHNICAL SKILLS)\}.*?)(?=\\section\{|\Z)",
        tex,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not section:
        return tex
    block = section.group(1)
    return tex.replace(block, SKILLS_PIPE.sub(", ", block))


def _fix_java_order(tex: str) -> str:
    if "Cognizant Technology Solutions" not in tex:
        return tex
    match = re.search(
        r"(\\section\{EXPERIENCE\}.*?\\resumeSubHeadingListStart\s*)"
        r"(.*?)"
        r"(\s*\\resumeSubHeadingListEnd)",
        tex,
        flags=re.DOTALL,
    )
    if not match:
        return tex
    body = match.group(2)
    usf = re.search(
        r"(\\resumeSubheading\s*\{University of South Florida\}.*?\\resumeItemListEnd)",
        body,
        flags=re.DOTALL,
    )
    cognizant = re.search(
        r"(\\resumeSubheading\s*\{Cognizant Technology Solutions\}.*?\\resumeItemListEnd)",
        body,
        flags=re.DOTALL,
    )
    if not usf or not cognizant:
        return tex
    if usf.start() < cognizant.start():
        return tex
    reordered = usf.group(1) + "\n\n" + cognizant.group(1)
    return tex[: match.start(2)] + reordered + tex[match.end(2) :]


def _upgrade_project_two_arg(tex: str) -> str:
    """Convert \\resumeProject{title}{stack} to three-arg with dates if missing."""

    def _add_date(match: re.Match[str]) -> str:
        title, stack = match.group(1), match.group(2)
        if re.search(r"\{[A-Za-z]{3}\s+\d{4}\s*--", stack):
            return match.group(0)
        default = "2024 -- 2024"
        if "Issue Tracking" in title:
            default = "Jan 2024 -- May 2024"
        elif "Student Enrollment" in title or "Enrollment and Course" in title:
            default = "Jun 2024 -- Aug 2024"
        elif "Task Board" in title:
            default = "Sep 2024 -- Nov 2024"
        elif "Job Market" in title or "Analytics Dashboard" in title:
            default = "Feb 2025 -- Apr 2025"
        elif "Code Review" in title:
            default = "Oct 2025 -- Feb 2026"
        elif "Content Aggregation" in title or "Event-Driven" in title:
            default = "Sep 2025 -- Jan 2026"
        elif "RAG" in title:
            default = "Jan 2025 -- Apr 2025"
        elif "Multi-Agent" in title:
            default = "May 2025 -- Aug 2025"
        elif "Prompt Registry" in title:
            default = "Sep 2025 -- Dec 2025"
        elif "LLM Infrastructure" in title or "MLOps" in title:
            default = "Jan 2026 -- Apr 2026"
        return f"\\resumeProject{{{title}}}{{{stack}}}{{{default}}}"

    return re.sub(
        r"\\resumeProject\{([^{}]+)\}\{([^{}]+)\}(?!\{)",
        _add_date,
        tex,
    )


def _upgrade_project_one_arg(tex: str) -> str:
    dates_by_title = {
        "Java Issue Tracking": ("Java, Spring Boot, React, PostgreSQL, JUnit", "Jan 2024 -- May 2024"),
        "RESTful Student Enrollment": ("Java, Spring Boot, PostgreSQL, Docker, GitHub Actions", "Jun 2024 -- Aug 2024"),
        "Production-Grade Hybrid RAG": ("Python, FastAPI, LangChain, Pinecone, pgvector", "Jan 2025 -- Apr 2025"),
        "Autonomous Multi-Agent": ("Python, FastAPI, LangGraph, PostgreSQL, Redis", "May 2025 -- Aug 2025"),
        "Centralized Prompt Registry": ("Python, FastAPI, React, PostgreSQL, Redis", "Sep 2025 -- Dec 2025"),
        "Scalable LLM Infrastructure": ("Docker, Kubernetes, Terraform, vLLM, Prometheus", "Jan 2026 -- Apr 2026"),
    }

    def _replace_one(match: re.Match[str]) -> str:
        title = match.group(1)
        for key, (stack, dates) in dates_by_title.items():
            if key in title:
                return f"\\resumeProject{{{title}}}{{{stack}}}{{{dates}}}"
        return f"\\resumeProject{{{title}}}{{See project bullets}}{{2024 -- 2024}}"

    return re.sub(r"\\resumeProject\{([^{}]+)\}(?!\{)", _replace_one, tex)


def patch_file(path: Path) -> None:
    tex = path.read_text(encoding="utf-8")
    tex = _replace_macros(tex)
    tex = HEADER_OLD.sub(HEADER_NEW, tex)
    tex = _comma_skills(tex)
    if "Software_Engineer_Java" in path.name:
        tex = _fix_java_order(tex)
    tex = _upgrade_project_two_arg(tex)
    tex = _upgrade_project_one_arg(tex)
    path.write_text(tex, encoding="utf-8")
    print(f"Patched {path.name}")


def main() -> None:
    for name in (
        "Tarun_Mannava_Software_Engineer_Java.tex",
        "Tarun_Mannava_Software_Engineer_Node_TypeScript.tex",
        "Tarun_Mannava_Software_Engineer_Python_TypeScript.tex",
        "Tarun_Mannava_AI_Engineer.tex",
    ):
        patch_file(SCRATCH / name)


if __name__ == "__main__":
    main()
