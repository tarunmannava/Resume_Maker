"""Industry detection disabled."""

from __future__ import annotations

from dataclasses import dataclass

CANONICAL_INDUSTRIES = (
    "Fintech",
    "Healthcare",
    "E-commerce",
    "Cybersecurity",
    "SaaS",
    "Edtech",
    "Media",
    "Supply Chain",
    "Automotive",
    "Government",
    "General Technology",
)


@dataclass
class IndustryDetectionResult:
    industry: str | None
    confidence: float
    scores: dict[str, float]


def normalize_industry(raw: str | None) -> str | None:
    return None


def detect_industry_from_text(
    job_description: str,
    company_context: str | None = None,
) -> IndustryDetectionResult:
    return IndustryDetectionResult(industry=None, confidence=0.0, scores={})
