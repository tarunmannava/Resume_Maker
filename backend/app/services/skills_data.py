"""Canonical SKILLS section templates loader and parser."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("uvicorn.error")

SKILLS_TEMPLATES_PATH = Path(__file__).resolve().parents[2] / "storage" / "Resources" / "skills_templates.json"


def load_skills_templates() -> dict[str, Any]:
    if not SKILLS_TEMPLATES_PATH.exists():
        logger.warning(f"Skills templates JSON file not found at {SKILLS_TEMPLATES_PATH}")
        return {}
    with open(SKILLS_TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


SKILLS_TEMPLATES: dict[str, Any] = load_skills_templates()


def get_skills_template_for_stack(stack: str) -> dict[str, Any] | None:
    key = stack.lower().strip() if stack else ""
    if key in ("java", "spring"):
        return SKILLS_TEMPLATES.get("java")
    if key in ("ai", "ai_engineer", "ai_platform_engineer", "ml", "ml_engineer"):
        return SKILLS_TEMPLATES.get("ai")
    if key in ("python", "fastapi", "django"):
        return SKILLS_TEMPLATES.get("python")
    if key in ("dotnet", ".net", "c#", "csharp"):
        return SKILLS_TEMPLATES.get("dotnet")
    if key in ("node", "node.js", "react", "typescript", "fullstack", "fullstack_engineer"):
        return SKILLS_TEMPLATES.get("node")
    return SKILLS_TEMPLATES.get("python")


def format_all_canonical_templates_for_prompt() -> str:
    lines = [
        "CANONICAL SKILLS TEMPLATES (SELECT THE BEST MATCH FOR THE JOB DESCRIPTION):",
        "Examine the Job Description and candidate resume, then select the SINGLE best-matching canonical SKILLS template from the 4 options below. Use its exact category layout, category names, and LaTeX formatting as the baseline for the `\\section{SKILLS}` section. Adapt the skills inside each category to match the job description, pruning irrelevant items.",
        "",
    ]
    for key, tmpl in SKILLS_TEMPLATES.items():
        name = tmpl.get("name", key.capitalize())
        raw = tmpl.get("raw_latex", "")
        lines.append(f"Option ({name}):")
        lines.append(raw)
        lines.append("")
    return "\n".join(lines)
