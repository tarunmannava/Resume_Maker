import json
import logging
import re
from collections import Counter

from ..core.config import get_settings
from ..models.schemas import KeywordItem

logger = logging.getLogger("uvicorn.error")

KEYWORD_CATALOG: dict[str, tuple[str, float]] = {
    # Languages
    "python": ("language", 5),
    "java": ("language", 5),
    "javascript": ("language", 4),
    "typescript": ("language", 4),
    "c++": ("language", 5),
    "c": ("language", 5),
    "c#": ("language", 4),
    "go": ("language", 4),
    "rust": ("language", 4),
    "sql": ("language", 4),
    "bash": ("language", 3),
    "shell": ("language", 3),
    # Frontend
    "react": ("frontend", 5),
    "next.js": ("frontend", 4),
    "angular": ("frontend", 5),
    "vue": ("frontend", 4),
    "html": ("frontend", 2),
    "css": ("frontend", 2),
    "redux": ("frontend", 3),
    "rxjs": ("frontend", 3),
    "tailwind": ("frontend", 2),
    # Backend/frameworks
    "backend": ("backend", 4),
    "backends": ("backend", 4),
    "api": ("backend", 4),
    "apis": ("backend", 4),
    "spring boot": ("backend", 5),
    "django": ("backend", 5),
    "django rest framework": ("backend", 5),
    "fastapi": ("backend", 4),
    "flask": ("backend", 4),
    "node.js": ("backend", 4),
    "express": ("backend", 4),
    "rest api": ("backend", 4),
    "restful": ("backend", 4),
    "graphql": ("backend", 4),
    "microservices": ("backend", 4),
    "asp.net": ("backend", 5),
    "asp.net core": ("backend", 5),
    ".net": ("backend", 4),
    ".net core": ("backend", 4),
    "razor pages": ("backend", 4),
    "entity framework": ("backend", 4),
    "linq": ("backend", 3),
    "sqlalchemy": ("backend", 4),
    "pydantic": ("backend", 4),
    "asyncio": ("backend", 4),
    "async": ("backend", 3),
    "asynchronous processing": ("backend", 4),
    "rabbitmq": ("backend", 4),
    "celery": ("backend", 4),
    # Data & Ingestion
    "data pipeline": ("data", 5),
    "data pipelines": ("data", 5),
    "data ingestion": ("data", 5),
    "ingestion": ("data", 4),
    "web scraping": ("data", 4),
    "scraping": ("data", 4),
    "structured data": ("data", 4),
    "data quality": ("data", 4),
    "data processing": ("data", 4),
    "playwright": ("data", 4),
    "beautifulsoup": ("data", 3),
    "selenium": ("data", 3),
    "pandas": ("data", 4),
    "numpy": ("data", 4),
    "spark": ("data", 5),
    "pyspark": ("data", 5),
    "hadoop": ("data", 4),
    "kafka": ("data", 5),
    "airflow": ("data", 5),
    "dbt": ("data", 4),
    "snowflake": ("data", 5),
    "bigquery": ("data", 5),
    "redshift": ("data", 5),
    "databricks": ("data", 5),
    "etl": ("data", 4),
    "data warehousing": ("data", 4),
    # Databases
    "postgresql": ("database", 4),
    "mysql": ("database", 4),
    "mongodb": ("database", 4),
    "redis": ("database", 3),
    "oracle": ("database", 3),
    "sql server": ("database", 3),
    "stored procedures": ("database", 3),
    "nosql": ("database", 4),
    "supabase": ("database", 3),
    # Reporting & BI
    "power bi": ("data", 4),
    "tableau": ("data", 4),
    "data modeling": ("data", 4),
    "data dictionary": ("data", 3),
    "reporting": ("data", 3),
    # Cloud/devops
    "aws": ("cloud", 5),
    "gcp": ("cloud", 5),
    "azure": ("cloud", 5),
    "cloudflare": ("cloud", 3),
    "cloudflare r2": ("cloud", 3),
    "s3": ("cloud", 3),
    "docker": ("devops", 4),
    "kubernetes": ("devops", 5),
    "terraform": ("devops", 4),
    "ci/cd": ("devops", 4),
    "github actions": ("devops", 3),
    "git": ("devops", 3),
    "github": ("devops", 3),
    "linux": ("devops", 3),
    "jenkins": ("devops", 3),
    # Systems/concepts
    "systems analysis": ("concept", 3),
    "data structures": ("concept", 4),
    "algorithms": ("concept", 4),
    "object-oriented": ("concept", 3),
    "oop": ("concept", 3),
    "concurrency": ("concept", 4),
    "multithreading": ("concept", 4),
    "memory management": ("concept", 5),
    "pointers": ("concept", 5),
    "embedded": ("concept", 5),
    "distributed systems": ("concept", 5),
    "system design": ("concept", 4),
    "performance": ("concept", 3),
    "scalability": ("concept", 3),
    "authentication": ("concept", 3),
    "authorization": ("concept", 3),
    "oauth2": ("concept", 3),
    "jwt": ("concept", 3),
    "orm": ("concept", 3),
    # Practices
    "agile": ("practice", 2),
    "scrum": ("practice", 2),
    "testing": ("practice", 3),
    "unit testing": ("practice", 3),
    "pytest": ("practice", 3),
    "junit": ("practice", 3),
    "open source": ("practice", 3),
    # AI Engineering
    "generative ai": ("ai", 5),
    "llm": ("ai", 5),
    "rag": ("ai", 5),
    "langchain": ("ai", 5),
    "langgraph": ("ai", 4),
    "llamaindex": ("ai", 4),
    "mcp": ("ai", 4),
    "model context protocol": ("ai", 4),
    "multi-agent": ("ai", 4),
    "hugging face": ("ai", 4),
    "prompt engineering": ("ai", 4),
    "vector database": ("ai", 5),
    "embeddings": ("ai", 4),
    "pinecone": ("ai", 4),
    "milvus": ("ai", 4),
    "weaviate": ("ai", 4),
    "chromadb": ("ai", 4),
    "nlp": ("ai", 4),
    "pytorch": ("ai", 4),
    "tensorflow": ("ai", 4),
    "openai api": ("ai", 4),
    "gemini api": ("ai", 4),
    "cursor": ("ai", 3),
    "claude code": ("ai", 3),
    "github copilot": ("ai", 3),
    "vs code": ("tool", 2),
    "visual studio code": ("tool", 2),
    "intellij": ("tool", 2),
    "vim": ("tool", 2),
    "neovim": ("tool", 2),
}

REQUIRED_MARKERS = (
    "required",
    "must have",
    "must-have",
    "requirement",
    "minimum",
    "need",
    "proficient",
    "what you'll do",
    "what you will do",
    "what we look for",
    "responsibilities",
    "qualifications",
)
PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "bonus points",
    "plus",
)
SENIORITY_TERMS = (
    "intern",
    "junior",
    "entry",
    "associate",
    "mid-level",
    "senior",
    "staff",
    "principal",
    "lead",
)


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("restful", "rest api")
    text = text.replace("rest apis", "rest api")
    text = text.replace("nodejs", "node.js")
    text = text.replace("postgres", "postgresql")
    text = text.replace("k8s", "kubernetes")
    text = text.replace("llms", "llm")
    text = text.replace("pyspark", "spark")
    text = text.replace("visual studio code", "vs code")
    text = text.replace("data pipelines", "data pipeline")
    text = text.replace("backends", "backend")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if re.match(r"^[a-z0-9 .+#/-]+$", term):
        return re.compile(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def clean_json_text(text: str) -> str:
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


def extract_keywords_with_ai(text: str) -> list[KeywordItem]:
    """Uses AI to extract domain concepts and tech requirements from unstructured JDs."""
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()

    system_instruction = (
        "You are an ATS Keyword Extraction and Job Analysis Engine.\n"
        "Extract 5 to 15 key technical skills, engineering concepts, methodologies, architectures, and tools from the job description.\n"
        "Return valid JSON array only, no markdown formatting. Each element must have:\n"
        "- 'term': lowercase string (e.g. 'data ingestion', 'data pipeline', 'web scraping', 'backend', 'data quality', 'python', 'sql', 'git')\n"
        "- 'category': one of 'backend', 'data', 'language', 'cloud', 'devops', 'concept', 'ai', 'frontend', 'practice', 'tool'\n"
        "- 'weight': float from 2.0 to 5.0 (core requirements = 5.0, high-value skills = 4.0, nice-to-haves = 3.0)\n"
        "- 'required': boolean (true if mentioned in requirements/what you do, false if optional/bonus)\n"
        "Example:\n"
        '[{"term": "data ingestion", "category": "data", "weight": 5.0, "required": true}, {"term": "web scraping", "category": "data", "weight": 4.0, "required": false}]'
    )
    prompt = f"Job Description:\n{text}"

    try:
        if provider == "gemini" and settings.gemini_api_key:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    max_output_tokens=400,
                ),
            )
            raw = clean_json_text(response.text or "")
            data = json.loads(raw)
            if isinstance(data, list):
                return [
                    KeywordItem(
                        term=normalize(item.get("term", "")),
                        category=item.get("category", "concept"),
                        weight=float(item.get("weight", 3.0)),
                        required=bool(item.get("required", False)),
                        evidence_count=1,
                    )
                    for item in data
                    if item.get("term")
                ]

        elif provider == "openai" and settings.openai_api_key:
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
            is_preset = bool(settings.openai_model and settings.openai_model.startswith("@"))
            messages = []
            if not is_preset:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            completion = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.1,
                max_tokens=400,
            )
            raw = clean_json_text(completion.choices[0].message.content or "")
            data = json.loads(raw)
            if isinstance(data, list):
                return [
                    KeywordItem(
                        term=normalize(item.get("term", "")),
                        category=item.get("category", "concept"),
                        weight=float(item.get("weight", 3.0)),
                        required=bool(item.get("required", False)),
                        evidence_count=1,
                    )
                    for item in data
                    if item.get("term")
                ]
    except Exception as exc:
        logger.warning("AI keyword extraction failed: %s", exc)

    return []


def extract_keywords(
    text: str, *, job_context: bool = False, use_ai: bool = True
) -> list[KeywordItem]:
    normalized = normalize(text)
    counts: Counter[str] = Counter()
    for term in KEYWORD_CATALOG:
        matches = keyword_pattern(term).findall(normalized)
        if matches:
            counts[term] = len(matches)

    lines = [normalize(line) for line in text.splitlines() if line.strip()]
    items: list[KeywordItem] = []
    seen_terms: set[str] = set()

    for term, count in counts.items():
        category, base_weight = KEYWORD_CATALOG[term]
        required = False
        preferred = False
        if job_context:
            for line in lines:
                if term in line:
                    required = any(marker in line for marker in REQUIRED_MARKERS)
                    preferred = any(marker in line for marker in PREFERRED_MARKERS)
                    if required or preferred:
                        break
        weight = base_weight
        if required:
            weight += 2
        elif preferred:
            weight = max(1, weight - 1)
        if count > 1:
            weight += min(2, count - 1)
        
        seen_terms.add(term)
        items.append(
            KeywordItem(
                term=term,
                category=category,
                weight=float(weight),
                required=required,
                evidence_count=count,
            )
        )

    # If in job context and few keywords found, supplement with AI extraction
    if job_context and (len(items) < 4) and use_ai:
        ai_items = extract_keywords_with_ai(text)
        for ai_item in ai_items:
            if ai_item.term not in seen_terms and len(ai_item.term) > 1:
                seen_terms.add(ai_item.term)
                items.append(ai_item)

    return sorted(items, key=lambda item: (-item.weight, item.category, item.term))


def seniority_signals(text: str) -> list[str]:
    lowered = normalize(text)
    return [term for term in SENIORITY_TERMS if term in lowered]
