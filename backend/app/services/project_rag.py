import json
import logging
import re
from typing import Any
from pathlib import Path
from openai import OpenAI

from ..core.config import get_settings

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "system", "platform", "production", "framework", "real", "time",
    "using", "with", "and", "the", "for", "are", "our", "out", "can",
    "has", "its", "that", "this", "from", "into", "across", "over",
}

# NOTE: must match the on-disk casing exactly ("Resources", capital R).
# This directory is looked up on case-sensitive filesystems (Linux/macOS
# deployment targets), where a mismatched case silently fails to find the
# projects/embeddings files.
RESOURCES_DIR = Path(__file__).resolve().parents[2] / "storage" / "Resources"
PROJECTS_FILE = RESOURCES_DIR / "projects.json"
EMBEDDINGS_FILE = RESOURCES_DIR / "project_embeddings.json"


def has_embedding_credentials() -> bool:
    """Whether an OpenAI-compatible embeddings call can plausibly succeed.

    The embeddings API is OpenAI-specific (`text-embedding-3-small`). Many
    valid app configurations (AI_PROVIDER=gemini with no OpenAI-compatible
    key, or OPENAI_BASE_URL pointed at a provider like OpenRouter that
    doesn't serve this embedding model) cannot use it at all. We check this
    upfront so we can skip straight to the lexical fallback instead of
    wasting a network round trip and logging a scary-looking error for
    what is actually an expected configuration.
    """
    settings = get_settings()
    if not (settings.openai_api_key or settings.openrouter_api_key):
        return False
    base_url = (settings.openai_base_url or "").lower()
    # Known providers that proxy chat completions but do not reliably serve
    # OpenAI's embedding models.
    non_embedding_hosts = ("openrouter.ai", "fireworks.ai", "nvidia.com")
    if any(host in base_url for host in non_embedding_hosts):
        return False
    return True


def get_embedding_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key or settings.openrouter_api_key,
        base_url=settings.openai_base_url
    )


def _tokenize(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"\b\w{3,}\b", text.lower())
        if word not in _STOPWORDS
    }


def score_project_lexically(project: dict[str, Any], job_description: str) -> float:
    """Deterministic, dependency-free relevance score used when embeddings
    are unavailable or fail. Weighs exact tech-stack mentions heavily and
    gives partial credit for general title/description word overlap so the
    fallback still points at the most relevant projects instead of an
    arbitrary fixed pair.
    """
    score = 0.0
    for tech in project.get("tech_stack", []):
        pattern = re.compile(rf"\b{re.escape(tech.lower())}\b", re.IGNORECASE)
        score += len(pattern.findall(job_description)) * 3.0

    desc_text = f"{project.get('title', '')} {project.get('description', '')}"
    desc_words = _tokenize(desc_text)
    jd_words = _tokenize(job_description)
    score += len(desc_words & jd_words)
    return score


def get_projects_by_lexical_relevance(
    job_description: str, projects: list[dict[str, Any]], top_k: int = 2
) -> list[dict[str, Any]]:
    scored = sorted(
        projects,
        key=lambda p: score_project_lexically(p, job_description),
        reverse=True,
    )
    return scored[:top_k]


def generate_embedding(text: str, client: OpenAI) -> list[float]:
    """Generate a vector embedding for a given text string."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        # Return empty vector if it fails (not ideal, but prevents crash)
        return []


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate the cosine similarity between two vectors using standard python math."""
    if not v1 or not v2:
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    mag1 = sum(x * x for x in v1) ** 0.5
    mag2 = sum(x * x for x in v2) ** 0.5
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)


def build_project_text_for_embedding(project: dict[str, Any]) -> str:
    """Combine the most important fields of a project into a dense semantic string for the embedding model."""
    title = project.get("title", "")
    tech_stack = ", ".join(project.get("tech_stack", []))
    bullets = " ".join(project.get("bullets", []))
    context = project.get("extra_context", "")
    
    # We want the embedding model to heavily weight the technical skills and the core architecture/context
    return f"Title: {title}\nTech Stack: {tech_stack}\nBullets: {bullets}\nContext: {context}"


def index_projects() -> bool:
    """Reads projects.json, generates embeddings, and saves to project_embeddings.json.
    This should be run whenever new projects are added to projects.json.

    Returns True on a usable index, False if embeddings could not be
    generated (e.g. no valid embeddings-capable API key configured). On
    failure we deliberately do NOT write a broken/all-empty embeddings file,
    since that would make the "missing file" auto-index check pass forever
    while every similarity score is stuck at 0.0.
    """
    if not PROJECTS_FILE.exists():
        logger.error(f"Could not find projects file at {PROJECTS_FILE}")
        return False

    if not has_embedding_credentials():
        logger.info(
            "No embeddings-capable API key configured; skipping embedding "
            "index. Project selection will use lexical relevance instead."
        )
        return False

    with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
        projects = json.load(f)

    client = get_embedding_client()
    embeddings_data = []

    logger.info(f"Generating embeddings for {len(projects)} projects...")
    for project in projects:
        project_id = project.get("id")
        text_to_embed = build_project_text_for_embedding(project)
        vector = generate_embedding(text_to_embed, client)
        embeddings_data.append({
            "id": project_id,
            "embedding": vector
        })

    if not any(item["embedding"] for item in embeddings_data):
        logger.error("Embedding generation returned no usable vectors; not writing index.")
        return False

    with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f)

    logger.info(f"Successfully indexed {len(projects)} projects and saved to {EMBEDDINGS_FILE}")
    return True


def get_relevant_projects(job_description: str, top_k: int = 2) -> list[dict[str, Any]]:
    """Retrieve the top_k most relevant projects for a given job description.

    Uses OpenAI embeddings + cosine similarity when a compatible API key is
    configured, and always falls back to a deterministic lexical relevance
    score (tech-stack + title/description overlap) so the JD -> relevant
    project matching keeps working even without embeddings.
    """
    if not PROJECTS_FILE.exists():
        logger.error(f"Projects file missing at {PROJECTS_FILE}")
        return []

    with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
        projects = json.load(f)

    if not has_embedding_credentials():
        return get_projects_by_lexical_relevance(job_description, projects, top_k)

    # Auto-index if embeddings file doesn't exist or is unusable
    if not EMBEDDINGS_FILE.exists():
        logger.info("Embeddings file missing. Running indexer now...")
        if not index_projects():
            return get_projects_by_lexical_relevance(job_description, projects, top_k)

    try:
        with open(EMBEDDINGS_FILE, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error(f"Could not read embeddings file, using lexical fallback: {exc}")
        return get_projects_by_lexical_relevance(job_description, projects, top_k)

    # Map embeddings to project IDs for fast lookup
    vector_map = {item["id"]: item["embedding"] for item in embeddings_data}

    client = get_embedding_client()
    jd_vector = generate_embedding(job_description, client)

    if not jd_vector:
        logger.warning("Failed to generate embedding for job description; using lexical fallback.")
        return get_projects_by_lexical_relevance(job_description, projects, top_k)

    scored_projects = [
        (cosine_similarity(jd_vector, vector_map.get(project.get("id"), [])), project)
        for project in projects
    ]
    scored_projects.sort(key=lambda x: x[0], reverse=True)

    if all(score == 0.0 for score, _ in scored_projects):
        logger.warning("All embedding similarity scores were 0.0; using lexical fallback.")
        return get_projects_by_lexical_relevance(job_description, projects, top_k)

    top_projects = [p for score, p in scored_projects[:top_k]]

    for i, (score, p) in enumerate(scored_projects[:top_k]):
        logger.info(f"RAG Match #{i+1}: '{p.get('name')}' (Score: {score:.3f})")

    return top_projects


if __name__ == "__main__":
    # If run directly as a script, index the projects
    index_projects()
