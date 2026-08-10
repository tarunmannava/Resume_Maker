# Specification: Dynamic Introductory Summary Adaptation Engine

## Overview
This track implements dynamic, role-aware and stack-aware introductory summary statement rewriting in the resume LaTeX header block. The system adapts the candidate's summary paragraph (`\textit{...}`) under the contact heading to match target job description requirements while preserving core backend software engineering credentials and defensible experience bounds.

## Functional Requirements

### 1. Hybrid Experience & Role Framing
- Dynamically rewrite the introductory summary statement under the LaTeX contact header block (`\begin{center}...\end{center}`).
- Retain the candidate's core "2+ years of software engineering experience" and backend engineering foundation (microservices, REST APIs, databases, cloud).
- When targeting **AI Engineer** or specialized roles:
  - Do NOT replace the candidate's backend engineering foundation.
  - Append/blend target expertise (e.g., "...with expertise in building AI platform tools, LLM workflows, RAG pipelines, and vector search using Python, FastAPI, and Docker.").
- For **Java**, **Python**, and **Node.js** targets, emphasize the corresponding target stack while maintaining production backend achievements.

### 2. Prompt Rule Updates (`rewrite.py`)
- Update `SYSTEM_PROMPT_BASE` and `build_user_prompt` in `backend/app/services/rewrite.py` with explicit, mandatory guidelines for header summary statement adaptation.
- Ensure the model outputs the summary in italicized LaTeX formatting (`\textit{...}`) directly under the contact header.

### 3. Verification & Testing
- Add unit test cases in `backend/tests/test_intro_summary.py` verifying that rewritten resumes contain hybrid backend + target role summary statements without losing core experience claims.

## Non-Functional Requirements
- **ATS & Formatting Compliance**: Retain LaTeX formatting, margins, and section structure without introducing unescaped LaTeX characters.
