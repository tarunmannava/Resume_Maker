import os
import sys
import time
import shutil
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.models.schemas import RewriteRequest
from backend.app.services.rewrite import rewrite_resume
from backend.app.services.docx import convert_tex_to_docx

BASE_RESUME_PATH = PROJECT_ROOT / "Tarun_Mannava_Resume.tex"
base_latex = BASE_RESUME_PATH.read_text(encoding="utf-8")

OUTPUT_DIR = PROJECT_ROOT / "generated_resumes"
OUTPUT_DIR.mkdir(exist_ok=True)

# 5 Target Specifications
SPECS = [
    {
        "name": ".NET Developer",
        "filename": "TarunMannava_DotnetDeveloper.docx",
        "role_name": "Senior .NET Developer",
        "jd": """
        Senior C# .NET Core Software Engineer
        Requirements:
        - 3+ years experience building enterprise microservices using C#, .NET 8 / ASP.NET Core, and Entity Framework Core.
        - Database engineering with SQL Server (T-SQL, complex indexing, query tuning) and MongoDB.
        - Automated unit and integration testing with xUnit, NUnit, and Moq.
        - Experience with RESTful Web APIs, Redis distributed caching, and CI/CD pipelines on Azure/Docker.
        - Experience with modern AI developer tools (Claude Code, Cursor, GitHub Copilot).
        """,
        "expected_stack": "dotnet",
        "must_have": ["C#", ".NET 8", "ASP.NET Core", "Entity Framework Core", "SQL Server", "MongoDB", "xUnit"],
        "must_not_have": ["Spring Boot", "Spring MVC", "jOOQ", "JUnit"],
    },
    {
        "name": "Java Software Engineer",
        "filename": "TarunMannava_SoftwareEngineer.docx",
        "role_name": "Senior Java Software Engineer",
        "jd": """
        Senior Java Software Engineer - Microservices & Distributed Systems
        Requirements:
        - 3+ years enterprise experience with Java 11/17, Spring Boot, Spring Data JPA, and Hibernate.
        - Microservices design, RESTful APIs, Redis caching, and asynchronous messaging with RabbitMQ.
        - Relational and NoSQL databases: PostgreSQL, MongoDB, SQL Server, and jOOQ query tuning.
        - Robust automated testing with JUnit 5, Mockito, and CI/CD automation.
        - Experience with AI developer productivity tools (Claude Code, Cursor, Copilot).
        """,
        "expected_stack": "java",
        "must_have": ["Java 11", "Spring Boot", "MongoDB", "SQL Server", "jOOQ", "JUnit 5", "RabbitMQ"],
        "must_not_have": [],
    },
    {
        "name": "Python Software Developer",
        "filename": "TarunMannava_SoftwareDeveloper.docx",
        "role_name": "Python Backend Software Developer",
        "jd": """
        Python Backend Software Developer
        Requirements:
        - 3+ years experience with Python 3.10+, FastAPI, Flask, AsyncIO, and Pydantic.
        - High-throughput asynchronous REST APIs, SQLAlchemy ORM, and PostgreSQL / MongoDB data modeling.
        - Asynchronous background task processing with RabbitMQ / Celery, Redis caching, and Docker.
        - Automated test-driven development using pytest and mock.
        - Familiarity with AI developer tools (Claude Code, Cursor, Copilot).
        """,
        "expected_stack": "python",
        "must_have": ["Python", "FastAPI", "AsyncIO", "SQLAlchemy", "PostgreSQL", "MongoDB", "RabbitMQ", "pytest"],
        "must_not_have": [],
    },
    {
        "name": "Node / Fullstack SE",
        "filename": "TarunMannava_SE.docx",
        "role_name": "Full Stack Software Engineer",
        "jd": """
        Full Stack Software Engineer (TypeScript / React / Node.js)
        Requirements:
        - Strong proficiency in TypeScript, Node.js, Express / NestJS, and React 18 / Next.js.
        - Developing scalable REST APIs, GraphQL, and event-driven architectures with RabbitMQ.
        - Database design with PostgreSQL, MongoDB, and Redis caching.
        - Building interactive frontend components with clean state management and responsive UI.
        - Automated testing using Jest, Supertest, and modern CI/CD workflows.
        """,
        "expected_stack": "node",
        "must_have": ["TypeScript", "Node.js", "React", "MongoDB", "PostgreSQL", "RabbitMQ", "SkillBeacon", "AutoDocs"],
        "must_not_have": [],
    },
    {
        "name": "AI / ML Engineer",
        "filename": "TarunMannava.docx",
        "role_name": "AI / Machine Learning Platform Engineer",
        "jd": """
        Senior AI / GenAI Platform Engineer
        Requirements:
        - Deep expertise in LLM applications, RAG pipelines, LangGraph, LangChain, and Multi-Agent Orchestration.
        - Hands-on experience with Model Context Protocol (MCP) and Agent-to-Agent (A2A) communication protocols.
        - Vector databases (Pinecone, Qdrant, ChromaDB) and semantic embedding search.
        - In-browser / edge AI inference with Transformers.js, ONNX, and WASM.
        - Backend development with Python, FastAPI, AsyncIO, RabbitMQ, and cloud infrastructure.
        """,
        "expected_stack": "ai",
        "must_have": ["LLM", "RAG", "LangGraph", "LangChain", "Model Context Protocol", "MCP", "Transformers.js", "RabbitMQ"],
        "must_not_have": [],
    },
]

def generate_and_audit_all():
    print("=" * 70)
    print("GENERATING & AUDITING 5 LIVE RESUMES WITH REWRITE PIPELINE")
    print("=" * 70)
    
    results = []
    
    for idx, spec in enumerate(SPECS, 1):
        print(f"\n[{idx}/5] Generating: {spec['filename']} ({spec['name']})...")
        start_time = time.time()
        
        req = RewriteRequest(
            job_description=spec["jd"],
            resume_latex=base_latex,
            role_name=spec["role_name"],
            rewrite_mode="transferable",
        )
        
        res = rewrite_resume(req)
        elapsed = time.time() - start_time
        latex = res.rewritten_latex
        
        # Save TeX and DOCX to generated_resumes/
        tex_path = OUTPUT_DIR / f"{spec['filename']}.tex"
        docx_path = OUTPUT_DIR / spec["filename"]
        root_docx_path = PROJECT_ROOT / spec["filename"]
        
        tex_path.write_text(latex, encoding="utf-8")
        convert_tex_to_docx(tex_path, docx_path)
        
        # Try copying to root if root file is not locked by MS Word
        try:
            shutil.copy2(docx_path, root_docx_path)
        except Exception as e:
            print(f"  -> [INFO] Root file {spec['filename']} locked by Word, saved in generated_resumes/{spec['filename']}")
        
        # Audit criteria
        audit_passed = True
        missing_must_haves = []
        found_forbidden = []
        
        for mh in spec["must_have"]:
            mh_escaped = mh.replace("#", r"\#")
            if mh.lower() not in latex.lower() and mh_escaped.lower() not in latex.lower():
                missing_must_haves.append(mh)
                audit_passed = False
                
        for mnh in spec["must_not_have"]:
            if mnh.lower() in latex.lower():
                found_forbidden.append(mnh)
                audit_passed = False
                
        # Verify projects in-place
        projects_preserved = ("SkillBeacon" in latex or "skillbeacon" in latex.lower()) and ("AutoDocs" in latex or "autodocs" in latex.lower())
        if not projects_preserved:
            audit_passed = False
            
        docx_size = docx_path.stat().st_size if docx_path.exists() else 0
        if docx_size < 5000:
            audit_passed = False
            
        print(f"  -> Generated in {elapsed:.1f}s | DOCX Size: {docx_size:,} bytes")
        print(f"  -> Match Score: {res.match_score:.1f}% | Target Met: {res.target_met}")
        print(f"  -> Projects Preserved: {projects_preserved}")
        if missing_must_haves:
            print(f"  -> [WARNING] Missing Must-Haves: {missing_must_haves}")
        if found_forbidden:
            print(f"  -> [WARNING] Found Forbidden Terms: {found_forbidden}")
        print(f"  -> Status: {'PASSED' if audit_passed else 'NEEDS ATTENTION'}")
        
        results.append({
            "spec": spec,
            "elapsed": elapsed,
            "score": res.match_score,
            "size": docx_size,
            "passed": audit_passed,
            "missing": missing_must_haves,
            "forbidden": found_forbidden,
            "docx_path": str(docx_path),
        })
        
    print("\n" + "=" * 70)
    print("FINAL SUMMARY OF ALL 5 RESUMES:")
    print("=" * 70)
    all_ok = True
    for r in results:
        status_str = "SUCCESS" if r["passed"] else "FAILED"
        if not r["passed"]:
            all_ok = False
        print(f"[{status_str}] {r['spec']['filename']:<35} | Stack: {r['spec']['expected_stack']:<7} | Score: {r['score']:.1f}% | Path: {r['docx_path']}")
        
    if all_ok:
        print("\n>>> ALL 5 RESUMES SUCCESSFULLY GENERATED AND AUDITED! <<<")
    else:
        print("\n>>> COMPLETED WITH AUDIT WARNINGS <<<")

if __name__ == "__main__":
    generate_and_audit_all()
