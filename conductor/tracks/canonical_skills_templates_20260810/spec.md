# Specification: Canonical LaTeX SKILLS Templates Storage & Dynamic Integration Engine

## Overview
This track implements canonical LaTeX `SKILLS` section storage and dynamic stack-aware skills injection across the backend resume rewrite pipeline. Candidate skills are formatted according to four predefined, production-grade LaTeX templates tailored for **Java Developer**, **AI Engineer**, **Python Backend Developer**, and **Node.js / Fullstack Developer**, which are pruned and customized against target job description requirements.

## Functional Requirements

### 1. Storage & Schema Definition
- Store 4 canonical `\section{SKILLS}` LaTeX templates in `backend/storage/Resources/skills_templates.json`.
- Create a Python data loader module `backend/app/services/skills_data.py` to parse and load the JSON templates cleanly into memory.
- The 4 templates encompass:
  1. **Java Developer / Backend**: Backend (Java, Spring Boot, Spring MVC, Spring Security, Spring Data JPA, Hibernate, REST APIs, Microservices), Concurrency (CompletableFuture, ExecutorService), Databases (PostgreSQL, MongoDB, SQL Server, Redis, jOOQ), Cloud & DevOps (AWS Cognito/S3, Docker, GitHub Actions, Linux), Testing (JUnit, Cucumber), Frontend (React, JavaScript, HTML, CSS).
  2. **AI Engineer**: Languages (Python, TypeScript, SQL, Java), LLM APIs (OpenAI, Anthropic, Groq, Gemini), AI & ML (LangChain, LlamaIndex, LangGraph, RAG, Prompt Engineering, Model Evaluation, Vector Search), Backend & Platform (FastAPI, Node.js, React, REST APIs, PostgreSQL, Redis, Docker, Kubernetes), Observability & MLOps (vLLM, Prometheus, Grafana, Terraform, GitHub Actions, AWS, GPU Inference), Developer Tools (Git, GitHub, Cursor, GitHub Copilot), Testing (Jest, JUnit).
  3. **Python Developer**: Languages (Python, TypeScript, SQL, JavaScript, Java), Backend (FastAPI, Flask, Pydantic, AsyncIO, REST APIs, Microservices), Data & Cloud (PostgreSQL, Supabase, MongoDB, Redis, AWS, Docker, GitHub Actions, Linux), Testing (pytest, JUnit), Frontend (React, Next.js).
  4. **Node.js / Fullstack**: Core (TypeScript, Node.js, JavaScript ES2022+, SQL, Python), Backend & APIs (Express.js, REST APIs, Socket.io, Microservices, Authentication, RBAC, Jest, Supertest), Frontend (React, Next.js, React Query, Tailwind CSS), Data & Infra (PostgreSQL, Redis, MongoDB, AWS, Docker, Kubernetes, GitHub Actions, Linux).

### 2. Backend Skills Selection & Pruning Engine
- Integrate `latex_skills.py` with `skills_data.py`:
  - Determine active stack (`java`, `ai`, `python`, `node`) from `selected_role_category` and `selected_stack_override` (or auto-detected stack).
  - Select the matching canonical `SKILLS` template as structural baseline.
  - Dynamically prune or prioritize skill items matching target Job Description requirements while maintaining strict template formatting, pipe separators, and category lines.
- Preserve original LaTeX pipe separator style (`$|$` vs `\;|\;`).

### 3. Verification & Testing
- Unit tests in `backend/tests/test_canonical_skills.py` verifying template loading, correct stack template selection, JD-based pruning, and pipe separator formatting.

## Non-Functional Requirements
- **ATS Compliance**: Strict LaTeX formatting with no unescaped characters or missing braces.
- **Performance**: Template retrieval and pruning < 10ms execution time.
