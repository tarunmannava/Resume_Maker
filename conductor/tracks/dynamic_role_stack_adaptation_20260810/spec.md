# Specification: Dynamic Base Resume & Stack-Aware Experience/Project Adaptation Engine

## Overview
This track implements dynamic, role-aware and stack-aware resume adaptation across the frontend UI and backend LLM/post-processing rewrite pipeline. The system adapts candidate work experience and technical projects according to target job requirements while enforcing strict boundaries on core employment history.

## Functional Requirements

### 1. Role Selection & Base Resume Management
- The frontend UI displays 2 primary target role options:
  1. `Java Developer`
  2. `AI Engineer / Software Engineer`
- The candidate provides **1 master base resume `.tex` template**.

### 2. Stack Detection & Hybrid Selection
- When `AI Engineer / Software Engineer` is selected:
  - Default: The backend automatically analyzes the Job Description to detect the dominant target stack:
    - **Node.js / React / TypeScript**
    - **Python**
    - **Java**
  - UI Toggle: The user is presented with a toggle pill in the UI displaying the auto-detected stack, with the ability to manually override/select `[Node.js]`, `[Python]`, or `[Java]`.

### 3. Work Experience Adaptation Rules
- **Cognizant Experience Guardrail**: The primary tech stack and language for Cognizant work experience MUST remain **Java-focused**. Bullets may be reworded for metric impact, but the underlying backend language MUST NOT be changed from Java.
- **USF Experience Adaptation**:
  - For **Java** target stack: Adapt USF experience bullets to emphasize Java/Spring Boot backend workflows.
  - For **Node.js** target stack: Adapt USF experience bullets to emphasize Node.js / React / TypeScript fullstack workflows.
  - For **Python** target stack: Adapt USF experience bullets to emphasize Python / FastAPI / data workflows.

### 4. Technical Projects Selection & Injection
- The project repository catalog in `projects.json` is configured with **2 AI projects** and **1 Java project**:
  - `project_1`: Codebase QA & Retrieval Assistant (Python/AST/pgvector/Ollama)
  - `project_2`: Automated PR Documentation Agent (Python/FastAPI/Pydantic/Celery)
  - `java_order_ledger`: High-Throughput Financial Order Ledger (Java 21/Spring Boot 3.3/Kafka/Redisson)
- For **Java** role targets: Inject the dedicated Java project + matching backend project.
- For **Node.js / Python / AI** targets: Dynamically inject matching projects and frame titles/bullets for the target stack and domain.

### 5. Technical Skills Section Sanitation & Reordering
- Dynamically adapt the `TECHNICAL SKILLS` section based on the target role and detected stack:
  - **Java Developer**: Prioritize Java 21, Spring Boot 3.3, Microservices, Kafka, SQL, Docker.
  - **AI Engineer**: Prioritize Python, LangChain, PyTorch, RAG, Vector Databases (pgvector), Ollama, Transformers.
  - **Software Engineer (Node/Python)**: Prioritize matching stack (Node.js/TypeScript/React or Python/FastAPI/PostgreSQL).

## Non-Functional Requirements
- **ATS Compliance**: Retain original LaTeX template formatting, macros, margins, pipe separators (`|`), dates, companies, and education.
- **Performance**: Response time for stack detection and strategy classification < 500ms before LLM generation.
