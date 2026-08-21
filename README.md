# Resume Rewriter (Resume Maker)

An AI-powered, ATS-focused LaTeX resume rewriting and optimization engine built with FastAPI and React. Resume Maker tailors professional LaTeX resumes for target job descriptions with high technical accuracy, defensible accomplishments, stack-aware project injection, FAANG-style bullet points, and multi-format compilation (PDF & DOCX).

---

## 🚀 Complete End-to-End Processing Workflow

```
[ Job Description + Company Context ] ────┐
                                         ├───> [ Job & Resume Analyzer ] ───> [ Keyword Scoring & Gap Analysis ]
[ Candidate LaTeX Resume Code ] ─────────┘               │
                                                         ▼
                                             [ Role Identity & Stack Lock ]
                                                         │
                                                         ▼
[ Screening Assistant ] <─────────────────── [ Advanced LLM Rewrite Engine ]
                                                         │ (FAANG X-Y-Z Bullets + Seniority Bounds)
                                                         ▼
                                             [ Post-Processing Pipeline v3 ]
                                              ├── 1. Canonical SKILLS Injection
                                              ├── 2. Experience Section Reordering
                                              ├── 3. Stack-Aware RAG Project Injection
                                              └── 4. LaTeX & Pipe Separator Sanitization
                                                         │
                                                         ▼
                                             [ Multi-Format Output Engine ]
                                              ├── PDF (latexmk / MiKTeX)
                                              └── DOCX (python-docx parser)
```

---

## 🛠️ Complete Feature & Subsystem Architecture

### 1. 🔍 Job & Resume Analysis Engine (`job_analyzer.py`, `keyword_extractor.py`, `industry_detector.py`)
- **Contextual Keyword Extraction**: Extracts required vs. preferred technical terms, frameworks, databases, and cloud platforms with evidence weights.
- **Seniority Signal Parsing**: Detects required seniority levels (`Junior`, `Mid`, `Senior`, `Staff`, `Lead`) from job descriptions.
- **Industry & Role Classification**: Detects target role identity (`Backend`, `Frontend`, `Fullstack`, `AI/ML`, `DevOps`, `Data Engineering`) and industry domain (`Fintech`, `Healthcare`, `E-Commerce`, `Cybersecurity`, `EdTech`, `Enterprise SaaS`) to frame metrics.
- **Target Stack Resolution**: Automatically resolves primary stack emphasis (e.g. `Java / Spring Boot`, `Python / FastAPI / AI`, `TypeScript / React / Node`).

### 2. 📊 Keyword Overlap & Gap Scoring (`scoring.py`)
- **Status Classification**: Evaluates resume keywords as **Exact**, **Transferable**, **Missing**, or **Unsupported**.
- **Risk Assessment**: Categorizes keyword match risks (`low`, `medium`, `high`).
- **High-Risk Substitution Guardrail**: Protects specialized skills (e.g., C/C++, Embedded Systems, pointers, memory management, Kubernetes, Terraform) from direct hallucination when unsupported by source experience. Emphasizes underlying paradigms (OOP, concurrency, performance, algorithms) instead.

### 3. 🤖 Advanced LLM Rewrite Engine (`rewrite.py`, `rewrite_strategy.py`, `prompts/`)
- **Multi-Provider Support**: Built-in support for Google Gemini (`google-genai` SDK) and OpenAI-compatible APIs (OpenAI, OpenRouter, Fireworks AI, DeepSeek).
- **4 Flexible Rewrite Modes**:
  - `strict`: Limits edits to direct evidence present in the original resume.
  - `transferable` (default): Bridges missing skills using defensible, transferable concepts.
  - `user_verified`: Directly incorporates candidate-confirmed skills.
  - `aggressive`: Maximizes ATS keyword density while respecting safety guardrails.
- **FAANG X-Y-Z Bullet Formula**: Enforces metric-backed accomplishments (*"Accomplished [X] as measured by [Y], by doing [Z]"*) starting with strong past-tense action verbs, inline technology weaving, scale indicators, and quantified outcomes (sub-10ms p95 latency, throughput multipliers, volume bounds).
- **Seniority Credibility Bounds**: Calibrates action verbs and scope specifically for early-to-mid career engineers (2-3 years experience) to ensure accomplishments sound natural and defensible in interviews.

### 4. 🧩 Post-Processing Pipeline v3 (`latex_skills.py`, `latex_projects.py`, `project_rag.py`, `project_framing.py`)
- **Canonical `SKILLS` Section Injection**: Dynamically injects formatted skill categories (`Languages`, `Frameworks`, `Developer Tools`) matching candidate experience and job targets across 4 canonical LaTeX template styles.
- **Role Experience Reordering**: Reorders and prioritizes experience sections based on target role relevance.
- **Stack-Aware RAG Project Injection**:
  - Semantic vector retrieval using OpenAI `text-embedding-3-small` embeddings (with automatic lexical tokenization fallback).
  - Selects, frames, and injects exactly 2 industry-aligned technical projects from project knowledge bases (`storage/Resources/projects.json`).
  - Strips AI jargon and enforces a 2-project cap.
- **LaTeX Pipe Separator & Macro Sanitization**: Preserves LaTeX formatting, escapes special characters (`%`, `&`, `_`), cleans pipe separators (`|`), and prevents broken macro output.

### 5. 📄 Multi-Format Compilation & Storage (`pdf.py`, `docx.py`)
- **Local PDF Compilation**: Runs `latexmk` / MiKTeX locally to compile valid LaTeX documents into production-grade PDFs.
- **Native DOCX Export**: Converts LaTeX document structure into cleanly styled Microsoft Word (`.docx`) documents using `python-docx`.
- **Candidate Application Storage**: Automatically saves builds under `backend/storage/generated/{Candidate}_{Company}_{Role}/`.

### 6. 💬 Application Screening Question Assistant (`screening.py`)
- **Tailored Recruiter Q&A**: Synthesizes job description, candidate experience, company context, and target role to generate clear, interview-defensible answers for application screening questions with advisory warnings when experience is limited.

### 7. 💻 Interactive Web Frontend (`frontend/src/`)
- **React + Vite Interface**: Sleek dark-mode dashboard with side-by-side LaTeX editor, live preview, keyword breakdown tables, confirmed skill checkboxes, screening question assistant, and multi-format download triggers (PDF / DOCX).

---

## 🏛️ Architecture & API Endpoints

| Endpoint | Method | Input Schema | Output / Description |
|---|---|---|---|
| `/api/health` | `GET` | — | System health check and module status. |
| `/api/analyze-job` | `POST` | `AnalyzeJobRequest` | Extracts keywords, seniority signals, role category, and industry from JD. |
| `/api/analyze-resume` | `POST` | `AnalyzeResumeRequest` | Parses LaTeX resume text, extracts sections, and highlights ATS warnings. |
| `/api/score` | `POST` | `ScoreRequest` | Scores keyword match against job requirements across rewrite modes. |
| `/api/rewrite` | `POST` | `RewriteRequest` | Executes full AI resume rewrite pipeline (skills, summary, projects, bullets). |
| `/api/compile` | `POST` | `CompileRequest` | Compiles LaTeX code locally into PDF format. |
| `/api/compile-docx` | `POST` | `CompileRequest` | Generates DOCX version of LaTeX resume code. |
| `/api/files/{folder}/{filename}` | `GET` | Path params | Serves compiled PDF or DOCX resume downloads. |
| `/api/screening/answer` | `POST` | `ScreeningAnswerRequest` | Generates tailored screening question responses. |

---

## ⚡ Quick Start

### Backend Setup

1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Copy environment template:
   ```bash
   copy backend\.env.example backend\.env
   ```

4. Configure your AI provider in `backend/.env`. Supported options include Gemini, OpenAI, or OpenRouter/Fireworks:
   - **Gemini**: Set `AI_PROVIDER=gemini` and provide `GEMINI_API_KEY`.
   - **OpenAI / OpenRouter**: Set `AI_PROVIDER=openai`, provide `OPENAI_API_KEY`, `OPENAI_BASE_URL` (e.g. `https://openrouter.ai/api/v1`), and `OPENAI_MODEL` (e.g. `deepseek/deepseek-v4-flash`).

5. Start FastAPI server from root directory:
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```
   Interactive API docs are accessible at `http://localhost:8000/docs`.

### Frontend Setup

1. Install dependencies:
   ```bash
   npm install --prefix frontend
   ```

2. Start development server:
   ```bash
   npm run dev --prefix frontend
   ```

3. Open the web interface at `http://localhost:5173`.

---

## 📁 Output Directory Structure

Generated PDF and DOCX files are organized per candidate application:

```
backend/storage/generated/{Candidate_Name}_{Company}_{Role}/
├── {Candidate_Name}_{Company}_{Role}.pdf
└── {Candidate_Name}_{Company}_{Role}.docx
```
