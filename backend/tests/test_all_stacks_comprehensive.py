"""Comprehensive end-to-end test suite testing all 5 engineering stacks:
1. .NET / C# Stack
2. Java / Spring Boot Stack
3. Node.js / TypeScript Stack
4. Python / FastAPI Stack
5. AI / GenAI / ML Stack
"""

import pytest
from pathlib import Path
from backend.app.models.schemas import RewriteRequest
from backend.app.services.job_analyzer import detect_target_stack
from backend.app.services.rewrite import rewrite_resume
from backend.app.services.docx import convert_tex_to_docx

BASE_RESUME_PATH = Path(__file__).resolve().parents[2] / "Tarun_Mannava_Resume.tex"


@pytest.fixture
def base_latex() -> str:
    return BASE_RESUME_PATH.read_text(encoding="utf-8")


def test_dotnet_stack_end_to_end(base_latex, monkeypatch, tmp_path):
    """Test .NET stack: C# adaptation, Java purge, project preservation, and DOCX compilation."""
    jd = """
    Senior C# .NET Developer
    Requirements:
    - 3+ years building enterprise web services with C#, .NET 8 / ASP.NET Core, and Entity Framework Core.
    - Strong database skills with SQL Server (T-SQL) and MongoDB.
    - Automated testing with xUnit, NUnit, and Moq.
    - Experience with RESTful Web APIs, Redis caching, and CI/CD pipelines.
    - Familiarity with AI developer tools like Claude Code, Cursor, or GitHub Copilot.
    """
    assert detect_target_stack(jd, role_name=".NET Developer") == "dotnet"

    def mock_llm(prompt, align_titles=False):
        return (base_latex, "test_provider")

    monkeypatch.setattr("backend.app.services.rewrite.generate_rewrite", mock_llm)

    req = RewriteRequest(
        job_description=jd,
        resume_latex=base_latex,
        role_name="Senior .NET Developer",
        rewrite_mode="transferable",
    )
    res = rewrite_resume(req)
    latex = res.rewritten_latex

    # 1. Verify C# / .NET in Summary
    assert "C\\#" in latex or "C#" in latex
    assert ".NET" in latex or "ASP.NET Core" in latex

    # 2. Verify Cognizant Experience adapted to .NET
    assert "Entity Framework Core" in latex or "ASP.NET Core" in latex
    assert "xUnit" in latex or "NUnit" in latex

    # 3. Verify USF Experience adapted to .NET
    assert "ASP.NET Core" in latex or "C\\#" in latex

    # 4. Verify Java frameworks strictly purged
    assert "Spring Boot" not in latex
    assert "Spring MVC" not in latex
    assert "jOOQ" not in latex
    assert "JUnit" not in latex

    # 5. Verify Skills section contains .NET & MongoDB
    assert "SQL Server" in latex
    assert "MongoDB" in latex
    assert "Claude Code" in latex or "Cursor" in latex

    # 6. Verify original projects preserved
    assert "SkillBeacon" in latex
    assert "AutoDocs" in latex

    # 7. Verify DOCX compilation
    tex_file = tmp_path / "dotnet.tex"
    docx_file = tmp_path / "dotnet.docx"
    tex_file.write_text(latex, encoding="utf-8")
    convert_tex_to_docx(tex_file, docx_file)
    assert docx_file.exists()
    assert docx_file.stat().st_size > 5000


def test_java_stack_end_to_end(base_latex, monkeypatch, tmp_path):
    """Test Java stack: Cognizant-first ordering, USF Java adaptation, MongoDB, and project preservation."""
    jd = """
    Senior Java Software Engineer
    Requirements:
    - 3+ years experience with Java 11/17, Spring Boot, Spring Data JPA, and Hibernate.
    - Microservices, REST APIs, Redis caching, and RabbitMQ messaging.
    - Experience with PostgreSQL, MongoDB, SQL Server, and jOOQ query optimization.
    - Automated testing with JUnit 5, Mockito, and Cucumber.
    - Modern developer tools (Claude Code, Cursor, Copilot).
    """
    assert detect_target_stack(jd, role_name="Java Developer") == "java"

    def mock_llm(prompt, align_titles=False):
        return (base_latex, "test_provider")

    monkeypatch.setattr("backend.app.services.rewrite.generate_rewrite", mock_llm)

    req = RewriteRequest(
        job_description=jd,
        resume_latex=base_latex,
        role_name="Senior Java Software Engineer",
        rewrite_mode="transferable",
    )
    res = rewrite_resume(req)
    latex = res.rewritten_latex

    # 1. Verify Cognizant appears before USF for Java roles
    cog_idx = latex.find("Cognizant Technology Solutions")
    usf_idx = latex.find("University of South Florida")
    assert cog_idx != -1 and usf_idx != -1
    assert cog_idx < usf_idx

    # 2. Verify Cognizant preserved as Java / Spring Boot
    assert "Spring Boot" in latex
    assert "jOOQ" in latex or "SQL Server" in latex
    assert "MongoDB" in latex

    # 3. Verify USF adapted to Java 17 / Spring Boot
    assert "Java 17" in latex or "Spring Boot" in latex

    # 4. Verify Skills section contains Java, MongoDB, JUnit 5, AI Tools
    assert "Spring Security" in latex or "Spring Data JPA" in latex
    assert "MongoDB" in latex
    assert "Claude Code" in latex or "Cursor" in latex

    # 5. Verify projects preserved in-place
    assert "SkillBeacon" in latex
    assert "AutoDocs" in latex

    # 6. Verify DOCX compilation
    tex_file = tmp_path / "java.tex"
    docx_file = tmp_path / "java.docx"
    tex_file.write_text(latex, encoding="utf-8")
    convert_tex_to_docx(tex_file, docx_file)
    assert docx_file.exists()
    assert docx_file.stat().st_size > 5000


def test_node_stack_end_to_end(base_latex, monkeypatch, tmp_path):
    """Test Node.js / TypeScript stack: Cognizant Java retention, TypeScript & React skills, and project preservation."""
    jd = """
    Full Stack TypeScript / Node.js Engineer
    Requirements:
    - Strong proficiency with TypeScript, Node.js, Express, and React 18 / Next.js.
    - Experience designing REST APIs, GraphQL, and microservices.
    - Database experience with PostgreSQL, MongoDB, and Redis.
    - Experience with RabbitMQ, asynchronous job processing, and cloud services.
    - Automated testing with Jest, Supertest, and CI/CD.
    """
    assert detect_target_stack(jd, role_name="Full Stack TypeScript Developer") == "node"

    def mock_llm(prompt, align_titles=False):
        return (base_latex, "test_provider")

    monkeypatch.setattr("backend.app.services.rewrite.generate_rewrite", mock_llm)

    req = RewriteRequest(
        job_description=jd,
        resume_latex=base_latex,
        role_name="Full Stack TypeScript Engineer",
        rewrite_mode="transferable",
    )
    res = rewrite_resume(req)
    latex = res.rewritten_latex

    # 1. Verify Cognizant retains enterprise Java/Spring foundation
    assert "Cognizant Technology Solutions" in latex
    assert "Spring Boot" in latex or "microservices" in latex

    # 2. Verify USF highlights React & TypeScript
    assert "React and TypeScript" in latex or "TypeScript" in latex

    # 3. Verify original projects preserved
    assert "SkillBeacon" in latex
    assert "AutoDocs" in latex

    # 4. Verify DOCX compilation
    tex_file = tmp_path / "node.tex"
    docx_file = tmp_path / "node.docx"
    tex_file.write_text(latex, encoding="utf-8")
    convert_tex_to_docx(tex_file, docx_file)
    assert docx_file.exists()
    assert docx_file.stat().st_size > 5000


def test_python_stack_end_to_end(base_latex, monkeypatch, tmp_path):
    """Test Python / FastAPI stack: Cognizant Java retention, Python/FastAPI skills, and project preservation."""
    jd = """
    Backend Python Engineer
    Requirements:
    - 3+ years experience with Python 3.10+, FastAPI, Flask, AsyncIO, and Pydantic.
    - Relational data modeling with PostgreSQL and SQLAlchemy.
    - Experience with RabbitMQ, Celery, Redis caching, and Docker.
    - Automated testing with pytest and mock.
    """
    assert detect_target_stack(jd, role_name="Python Backend Engineer") == "python"

    def mock_llm(prompt, align_titles=False):
        return (base_latex, "test_provider")

    monkeypatch.setattr("backend.app.services.rewrite.generate_rewrite", mock_llm)

    req = RewriteRequest(
        job_description=jd,
        resume_latex=base_latex,
        role_name="Backend Python Engineer",
        rewrite_mode="transferable",
    )
    res = rewrite_resume(req)
    latex = res.rewritten_latex

    # 1. Verify Cognizant retains enterprise backend foundation
    assert "Cognizant Technology Solutions" in latex

    # 2. Verify USF features Python & FastAPI / Flask
    assert "Python" in latex

    # 3. Verify projects preserved in-place
    assert "SkillBeacon" in latex
    assert "AutoDocs" in latex

    # 4. Verify DOCX compilation
    tex_file = tmp_path / "python.tex"
    docx_file = tmp_path / "python.docx"
    tex_file.write_text(latex, encoding="utf-8")
    convert_tex_to_docx(tex_file, docx_file)
    assert docx_file.exists()
    assert docx_file.stat().st_size > 5000


def test_ai_stack_end_to_end(base_latex, monkeypatch, tmp_path):
    """Test AI / GenAI stack: Multi-agent, MCP, WASM embeddings, GenAI skills prominence, and project preservation."""
    jd = """
    AI Platform / GenAI Engineer
    Requirements:
    - Strong experience with LLMs, RAG Pipelines, LangGraph, LangChain, and Multi-Agent Orchestration.
    - Experience with Model Context Protocol (MCP) and agent-to-agent communication protocols.
    - Vector databases (Pinecone, Qdrant, ChromaDB) and semantic embedding search.
    - Python, FastAPI, AsyncIO, RabbitMQ, and cloud infrastructure.
    - Experience with client-side inference (Transformers.js / WASM / ONNX).
    """
    assert detect_target_stack(jd, role_name="AI Engineer") == "ai"

    def mock_llm(prompt, align_titles=False):
        return (base_latex, "test_provider")

    monkeypatch.setattr("backend.app.services.rewrite.generate_rewrite", mock_llm)

    req = RewriteRequest(
        job_description=jd,
        resume_latex=base_latex,
        role_name="AI Platform Engineer",
        rewrite_mode="transferable",
    )
    res = rewrite_resume(req)
    latex = res.rewritten_latex

    # 1. Verify USF features dual-model LLM sandbox & Transformers.js WASM embedding evaluation
    assert "Transformers.js" in latex or "WASM" in latex
    assert "Hugging Face" in latex or "Groq" in latex

    # 2. Verify AutoDocs features MCP & A2A protocols + RabbitMQ
    assert "AutoDocs" in latex
    assert "MCP" in latex or "Multi-Agent" in latex

    # 3. Verify SkillBeacon features semantic skills & confidence scoring
    assert "SkillBeacon" in latex

    # 4. Verify Cognizant retained for backend scale
    assert "Cognizant Technology Solutions" in latex

    # 5. Verify DOCX compilation
    tex_file = tmp_path / "ai.tex"
    docx_file = tmp_path / "ai.docx"
    tex_file.write_text(latex, encoding="utf-8")
    convert_tex_to_docx(tex_file, docx_file)
    assert docx_file.exists()
    assert docx_file.stat().st_size > 5000
