import re
import json
from google import genai
from google.genai import types
from openai import OpenAI

from ..core.config import get_settings
from .industry_detector import (
    CANONICAL_INDUSTRIES,
    detect_industry_from_text,
    normalize_industry,
)

# Backward-compatible export for tests/imports that referenced INDUSTRY_KEYWORDS
INDUSTRY_KEYWORDS = {name: [] for name in CANONICAL_INDUSTRIES if name != "General Technology"}

ROLE_KEYWORDS = {
    "AI Engineer": [
        r"\bgenerative ai\b", r"\bllm\b", r"\bllms\b", r"\brag\b", r"\blangchain\b",
        r"\bllamaindex\b", r"\bprompt engineering\b", r"\bvector database\b", r"\bopenai\b",
        r"\bgeminiai\b", r"\bclaude\b", r"\bcohere\b", r"\bvector search\b", r"\bai engineer\b"
    ],
    "AI Support": [
        r"\bmlops\b", r"\bml infrastructure\b", r"\bai infrastructure\b", r"\bgpu scheduling\b",
        r"\bvllm\b", r"\btgi\b", r"\bmodel serving\b", r"\bmodel deployment\b", r"\bplatform engineer\b",
        r"\binfrastructure engineer\b", r"\bdevops engineer\b"
    ],
    "ML Engineer": [
        r"\bmachine learning\b", r"\bml engineer\b", r"\bdeep learning\b", r"\bpytorch\b",
        r"\btensorflow\b", r"\bscikit-learn\b", r"\bxgboost\b", r"\blightgbm\b", r"\bpandas\b",
        r"\bnumpy\b", r"\bmodel training\b", r"\bclassification\b", r"\brecommendation\b",
        r"\brecommender\b", r"\bsemantic retrieval\b"
    ],
    "Software Engineer": [
        r"\bbackend\b", r"\bfrontend\b", r"\bfull stack\b", r"\bsoftware engineer\b",
        r"\bsoftware developer\b", r"\bweb application\b", r"\bapi\b", r"\bmicroservices\b",
        r"\bdatabase\b", r"\bjava\b", r"\bpython\b", r"\bgo\b", r"\bjavascript\b", r"\btypescript\b"
    ]
}

def detect_industry_with_keywords(
    job_description: str,
    company_context: str | None = None,
) -> tuple[str | None, float]:
    result = detect_industry_from_text(job_description, company_context)
    return result.industry, result.confidence


def detect_details_with_keywords(text: str) -> tuple[str | None, str]:
    # 1. Detect Industry (weighted signals — do not use bare "health", "auth", etc.)
    detected_industry, _ = detect_industry_with_keywords(text, None)

    # 2. Detect Role Category
    text_lower = text.lower()
    role_scores = {}
    for role, patterns in ROLE_KEYWORDS.items():
        score = 0
        for pattern in patterns:
            score += len(re.findall(pattern, text_lower))
        role_scores[role] = score
        
    detected_role = "Software Engineer" # Default
    if role_scores and max(role_scores.values()) > 0:
        detected_role = max(role_scores, key=role_scores.get)
        
    return detected_industry, detected_role

def clean_json_text(text: str) -> str:
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
    return text

def detect_details_with_ai(job_description: str, company_context: str | None = None) -> tuple[str | None, str]:
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()
    
    industry_enum = ", ".join(
        f'"{name}"' for name in CANONICAL_INDUSTRIES if name != "General Technology"
    )
    system_instruction = (
        "You are a recruiting intelligence assistant. Analyze the job description and optional company context.\n"
        "1. Identify the role category. It MUST be exactly one of: 'Software Engineer', 'AI Engineer', 'AI Support', 'ML Engineer'.\n"
        f"2. Identify the company's PRIMARY business industry. It MUST be exactly one of: {industry_enum}, or null.\n"
        "   - Infer from what the company sells or regulates (e.g. hospital → Healthcare, bank → Fintech), NOT from generic tech words.\n"
        "   - Do NOT classify as Healthcare for 'health checks' or uptime. Do NOT classify as Cybersecurity for app login/JWT/Spring Security alone.\n"
        "   - Do NOT classify as Edtech for machine learning / deep learning. Return null if unclear.\n"
        "Return valid JSON only, no markdown. Example:\n"
        '{"role_category": "Software Engineer", "industry": "Healthcare", "confidence": 0.9}'
    )
    
    prompt = f"Job Description:\n{job_description}\n\nCompany Context:\n{company_context or 'None'}"
    
    try:
        if provider == "gemini" and settings.gemini_api_key:
            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    max_output_tokens=150,
                ),
            )
            raw_text = clean_json_text(response.text or "")
            data = json.loads(raw_text)
            industry = normalize_industry(data.get("industry"))
            return industry, data.get("role_category", "Software Engineer")

        elif provider == "openai" and settings.openai_api_key:
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
            completion = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=150,
            )
            raw_text = clean_json_text(completion.choices[0].message.content or "")
            data = json.loads(raw_text)
            industry = normalize_industry(data.get("industry"))
            return industry, data.get("role_category", "Software Engineer")

    except Exception:
        pass  # Fallback below

    return detect_details_with_keywords(job_description + "\n" + (company_context or ""))


def resolve_industry(
    job_description: str,
    company_context: str | None = None,
    user_selected: str | None = None,
) -> tuple[str, float, str]:
    """
    Hybrid industry resolution. Returns (industry, confidence 0-1, source).
    source is one of: user, keywords, ai, default
    """
    if user_selected and user_selected.strip().lower() not in ("don't know", ""):
        return user_selected.strip(), 1.0, "user"

    kw_result = detect_industry_from_text(job_description, company_context)
    ai_industry, _ = detect_details_with_ai(job_description, company_context)
    ai_norm = normalize_industry(ai_industry)

    # High-confidence keyword match wins (fast, fewer false positives than before)
    if kw_result.industry and kw_result.confidence >= 0.55:
        return kw_result.industry, kw_result.confidence, "keywords"

    # AI when keywords are weak but AI returned a canonical industry
    if ai_norm and (not kw_result.industry or kw_result.confidence < 0.45):
        return ai_norm, 0.65, "ai"

    # Moderate keyword match
    if kw_result.industry and kw_result.confidence >= 0.35:
        return kw_result.industry, kw_result.confidence, "keywords"

    if ai_norm:
        return ai_norm, 0.5, "ai"

    return "General Technology", 0.0, "default"
