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
    if key in ("node", "node.js", "react", "typescript", "fullstack", "fullstack_engineer"):
        return SKILLS_TEMPLATES.get("node")
    return SKILLS_TEMPLATES.get("python")
