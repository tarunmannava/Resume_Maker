import re
from collections import Counter

from ..models.schemas import KeywordItem

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
    # Frontend
    "react": ("frontend", 5),
    "angular": ("frontend", 5),
    "vue": ("frontend", 4),
    "html": ("frontend", 2),
    "css": ("frontend", 2),
    "redux": ("frontend", 3),
    "rxjs": ("frontend", 3),
    "tailwind": ("frontend", 2),
    # Backend/frameworks
    "spring boot": ("backend", 5),
    "django": ("backend", 5),
    "django rest framework": ("backend", 5),
    "fastapi": ("backend", 4),
    "flask": ("backend", 4),
    "node.js": ("backend", 4),
    "express": ("backend", 4),
    "rest api": ("backend", 4),
    "graphql": ("backend", 4),
    "microservices": ("backend", 4),
    # Databases
    "postgresql": ("database", 4),
    "mysql": ("database", 4),
    "mongodb": ("database", 4),
    "redis": ("database", 3),
    "oracle": ("database", 3),
    "sql server": ("database", 3),
    # Cloud/devops
    "aws": ("cloud", 5),
    "gcp": ("cloud", 5),
    "azure": ("cloud", 5),
    "docker": ("devops", 4),
    "kubernetes": ("devops", 5),
    "terraform": ("devops", 4),
    "ci/cd": ("devops", 4),
    "github actions": ("devops", 3),
    "jenkins": ("devops", 3),
    # Systems/concepts
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
    "orm": ("concept", 3),
    # Practices
    "agile": ("practice", 2),
    "scrum": ("practice", 2),
    "testing": ("practice", 3),
    "unit testing": ("practice", 3),
    # Data Engineering
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
    "data pipeline": ("data", 4),
    "data warehousing": ("data", 4),
    "nosql": ("database", 4),
    # AI Engineering
    "generative ai": ("ai", 5),
    "llm": ("ai", 5),
    "rag": ("ai", 5),
    "langchain": ("ai", 5),
    "llamaindex": ("ai", 4),
    "hugging face": ("ai", 4),
    "prompt engineering": ("ai", 4),
    "vector database": ("ai", 5),
    "pinecone": ("ai", 4),
    "milvus": ("ai", 4),
    "weaviate": ("ai", 4),
    "chromadb": ("ai", 4),
    "nlp": ("ai", 4),
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
)
PREFERRED_MARKERS = ("preferred", "nice to have", "nice-to-have", "bonus", "plus")
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
    text = text.replace("nodejs", "node.js")
    text = text.replace("postgres", "postgresql")
    text = text.replace("k8s", "kubernetes")
    text = text.replace("llms", "llm")
    text = text.replace("pyspark", "spark")
    text = text.replace("visual studio code", "vs code")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if re.match(r"^[a-z0-9 .+#/-]+$", term):
        return re.compile(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def extract_keywords(text: str, *, job_context: bool = False) -> list[KeywordItem]:
    normalized = normalize(text)
    counts: Counter[str] = Counter()
    for term in KEYWORD_CATALOG:
        matches = keyword_pattern(term).findall(normalized)
        if matches:
            counts[term] = len(matches)

    lines = [normalize(line) for line in text.splitlines() if line.strip()]
    items: list[KeywordItem] = []
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
        items.append(
            KeywordItem(
                term=term,
                category=category,
                weight=float(weight),
                required=required,
                evidence_count=count,
            )
        )
    return sorted(items, key=lambda item: (-item.weight, item.category, item.term))


def seniority_signals(text: str) -> list[str]:
    lowered = normalize(text)
    return [term for term in SENIORITY_TERMS if term in lowered]
