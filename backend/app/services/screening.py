import logging

from google import genai
from google.genai import types
from openai import OpenAI

from ..core.config import get_settings
from .latex import latex_to_text

logger = logging.getLogger("uvicorn.error")

ANSWER_SYSTEM = """You are a job application assistant helping a candidate answer screening questions on job application forms.

Rules:
- Ground every claim in the candidate's resume. Do not invent employers, projects, metrics, or skills.
- Align answers to the target job description and role.
- Write in first person, professional but natural tone suitable for application text boxes.
- Be concise: 2-5 sentences for short-answer fields; up to 8 sentences for "tell us about yourself" style prompts.
- If the resume lacks direct evidence, acknowledge transferable experience honestly without fabricating.
- Do not use markdown, bullet lists, or headers unless the question explicitly asks for a list.
- Return only the answer text, no preamble or meta commentary."""


def _call_llm(system: str, prompt: str, max_tokens: int = 2048) -> str | None:
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()

    try:
        if provider == "gemini" and settings.gemini_api_key:
            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.35,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text

        if provider == "openai" and settings.openai_api_key:
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
            kwargs = {
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.35,
                "max_tokens": max_tokens,
            }
            if settings.openai_base_url and "openrouter.ai" in settings.openai_base_url:
                kwargs["extra_body"] = {"reasoning": {"enabled": True}}
            completion = client.chat.completions.create(**kwargs)
            return completion.choices[0].message.content
    except Exception as exc:
        logger.warning("Screening LLM call failed: %s", exc)

    return None


def _build_context_prompt(
    resume_text: str,
    job_description: str,
    *,
    company_context: str | None = None,
    role_name: str | None = None,
    company_name: str | None = None,
) -> str:
    parts = []
    if role_name or company_name:
        parts.append(f"Target role: {role_name or 'Not specified'} at {company_name or 'Not specified'}")
    parts.append(f"Job Description:\n{job_description}")
    if company_context:
        parts.append(f"Company Context:\n{company_context}")
    parts.append(f"Candidate Resume (plain text):\n{resume_text}")
    return "\n\n".join(parts)


def answer_screening_question(
    resume_latex: str,
    job_description: str,
    question: str,
    *,
    company_context: str | None = None,
    role_name: str | None = None,
    company_name: str | None = None,
) -> tuple[str, str | None]:
    resume_text = latex_to_text(resume_latex)
    prompt = _build_context_prompt(
        resume_text,
        job_description,
        company_context=company_context,
        role_name=role_name,
        company_name=company_name,
    )
    prompt += f"\n\nScreening question to answer:\n{question.strip()}"

    raw = _call_llm(ANSWER_SYSTEM, prompt, max_tokens=1024)
    if raw and raw.strip():
        return raw.strip(), None

    return (
        "Unable to generate an answer. Check that your AI provider API key is configured in the backend.",
        "AI unavailable",
    )
