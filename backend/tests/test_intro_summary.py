import pytest
from backend.app.prompts.rewrite_prompts import SYSTEM_PROMPT_BASE


def test_system_prompt_contains_intro_summary_adaptation_rules():
    assert "INTRODUCTORY SUMMARY STATEMENT ADAPTATION" in SYSTEM_PROMPT_BASE
    assert "MANDATORY HYBRID FRAMING RULE" in SYSTEM_PROMPT_BASE
    assert "2+ years of software engineering experience" in SYSTEM_PROMPT_BASE
    assert "expertise in AI platform engineering" in SYSTEM_PROMPT_BASE
