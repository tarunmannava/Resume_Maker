from backend.app.services import project_rag


SAMPLE_PROJECTS = [
    {
        "id": "backend_project",
        "name": "Java Backend Project",
        "title": "Java Spring Boot REST API Platform",
        "tech_stack": ["Java", "Spring Boot", "PostgreSQL"],
        "bullets": ["Built REST APIs with Spring Boot and PostgreSQL."],
        "description": "A backend REST API platform for enterprise workflows.",
    },
    {
        "id": "ai_project",
        "name": "LLM RAG Project",
        "title": "Hybrid RAG Support Assistant",
        "tech_stack": ["Python", "LangChain", "Pinecone"],
        "bullets": ["Built a hybrid RAG pipeline with LangChain."],
        "description": "A retrieval-augmented generation assistant using vector search.",
    },
]


def test_lexical_relevance_prefers_matching_tech_stack():
    jd = "We need a Java Spring Boot backend engineer to build REST APIs with PostgreSQL."
    ranked = project_rag.get_projects_by_lexical_relevance(jd, SAMPLE_PROJECTS, top_k=1)
    assert ranked[0]["id"] == "backend_project"


def test_lexical_relevance_prefers_ai_stack_for_llm_jd():
    jd = "Looking for an AI engineer experienced with LangChain, RAG pipelines, and vector databases like Pinecone."
    ranked = project_rag.get_projects_by_lexical_relevance(jd, SAMPLE_PROJECTS, top_k=1)
    assert ranked[0]["id"] == "ai_project"


def test_get_relevant_projects_falls_back_to_lexical_without_embedding_credentials(monkeypatch):
    """When no embeddings-capable API key is configured (e.g. AI_PROVIDER=gemini
    with no OpenAI-compatible key), project selection must still respond to the
    JD instead of silently returning a fixed/arbitrary pair."""
    monkeypatch.setattr(project_rag, "has_embedding_credentials", lambda: False)

    def fake_open(path, *args, **kwargs):
        import io
        import json as json_module

        return io.StringIO(json_module.dumps(SAMPLE_PROJECTS))

    monkeypatch.setattr("builtins.open", fake_open)

    jd = "Java Spring Boot backend engineer building REST APIs with PostgreSQL."
    results = project_rag.get_relevant_projects(jd, top_k=1)
    assert results[0]["id"] == "backend_project"
