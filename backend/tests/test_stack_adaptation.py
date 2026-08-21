import pytest
from backend.app.services.job_analyzer import detect_target_stack
from backend.app.services.project_framing import build_stack_experience_framing_instructions


def test_detect_target_stack_dotnet():
    jd = "Experience with tools and technologies such as Microsoft .NET, C#, SQL, REST APIs, Power Platform, Power Apps, SharePoint Online."
    assert detect_target_stack(jd) == "dotnet"


def test_detect_target_stack_java():
    jd = "We are hiring a Senior Java Developer with Spring Boot 3.3, Microservices, and PostgreSQL."
    assert detect_target_stack(jd) == "java"


def test_detect_target_stack_node():
    jd = "Looking for a Full Stack Engineer with Node.js, React, TypeScript, and Express."
    assert detect_target_stack(jd) == "node"


def test_detect_target_stack_python():
    jd = "Hiring a Backend Python Engineer with Python 3.11, FastAPI, AsyncIO, and PostgreSQL."
    assert detect_target_stack(jd) == "python"


def test_detect_target_stack_ai():
    jd = "Hiring an AI Engineer with Python, LLMs, LangChain, RAG pipelines, and vector search."
    assert detect_target_stack(jd) == "ai"


def test_detect_target_stack_manual_override():
    jd = "We are hiring a Senior Java Developer with Spring Boot."
    # Manual override forces node or dotnet
    assert detect_target_stack(jd, user_override="node") == "node"
    assert detect_target_stack(jd, user_override="dotnet") == "dotnet"
    assert detect_target_stack(jd, user_override="C#") == "dotnet"


def test_cognizant_java_guardrail_present():
    instructions = build_stack_experience_framing_instructions("node")
    assert "COGNIZANT EXPERIENCE GUARDRAIL" in instructions
    assert "Cognizant MUST remain Java-focused" in instructions
    assert "NEVER replace Java with Node.js or Python" in instructions

    dotnet_instructions = build_stack_experience_framing_instructions("dotnet")
    assert "COGNIZANT EXPERIENCE (.NET / C# TARGET STACK)" in dotnet_instructions
    assert "C# / .NET, ASP.NET Core" in dotnet_instructions


def test_usf_stack_adaptation_instructions():
    dotnet_instructions = build_stack_experience_framing_instructions("dotnet")
    assert "MUST STAY Python" in dotnet_instructions
    assert "Do NOT rewrite USF or projects into .NET/C#" in dotnet_instructions

    java_instructions = build_stack_experience_framing_instructions("java")
    assert "MUST STAY Python" in java_instructions
    assert "Do NOT rewrite USF or projects into Java" in java_instructions

    node_instructions = build_stack_experience_framing_instructions("node")
    assert "Node.js, TypeScript, React" in node_instructions

    python_instructions = build_stack_experience_framing_instructions("python")
    assert "Python, FastAPI" in python_instructions

    ai_instructions = build_stack_experience_framing_instructions("ai")
    assert "Python, LLMs, RAG" in ai_instructions


def test_detect_target_stack_with_role_name():
    jd = "Build dashboards and data visualizations with Power BI, SQL Server, and REST APIs."
    # Role name explicitly specifying .NET forces dotnet stack
    assert detect_target_stack(jd, role_name=".NET Developer") == "dotnet"
    assert detect_target_stack(jd, role_name="Senior C# Software Engineer") == "dotnet"
    assert detect_target_stack(jd, role_name="Java Backend Engineer") == "java"
    assert detect_target_stack(jd, role_name="Full Stack TypeScript Developer") == "node"


def test_adapt_resume_for_dotnet_purges_java():
    from backend.app.models.schemas import RewriteRequest
    from backend.app.services.rewrite import adapt_resume_for_dotnet

    java_resume = r"""
\documentclass{article}
\begin{document}
\begin{center}
{\Huge \textbf{Tarun Mannava}} \\
\textit{Software Engineer with 3+ years of experience building Java and Spring Boot applications.}
\end{center}
\section{SKILLS}
\begin{itemize}\item Java, Spring Boot, Spring MVC, Spring Security, jOOQ, JUnit, PostgreSQL\end{itemize}
\section{EXPERIENCE}
\begin{itemize}
\resumeSubheading{Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
\resumeItemListStart
\resumeItem{Developed Java 11/Spring Boot microservices for policy onboarding and validation.}
\resumeItemListEnd
\end{itemize}
\end{document}
"""
    req = RewriteRequest(
        job_description="C# .NET Developer role",
        resume_latex=java_resume,
        role_name=".NET Developer",
    )
    dotnet_resume = adapt_resume_for_dotnet(java_resume, req)

    assert "C\\#" in dotnet_resume or "C#" in dotnet_resume
    assert ".NET 8" in dotnet_resume or "ASP.NET Core" in dotnet_resume
    assert "Spring Boot" not in dotnet_resume
    assert "Spring MVC" not in dotnet_resume
    assert "JUnit" not in dotnet_resume
    assert "jOOQ" not in dotnet_resume

