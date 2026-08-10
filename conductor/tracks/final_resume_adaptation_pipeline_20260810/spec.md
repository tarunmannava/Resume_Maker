# Specification: Final Resume Adaptation & Stack-Aware Project Pipeline

## Overview
This track finalizes the end-to-end resume adaptation pipeline. It enforces Cognizant-first experience section ordering for Java Developer roles, locks Java project preservation in the template for Java applications, and executes deterministic replacement with `projects.json` catalog projects (with Node/TypeScript stack adaptation for JS roles) for non-Java applications.

## Functional Requirements

### 1. Java Role Experience Ordering
- When the target stack is **Java** (`selected_stack_override == 'java'` or detected Java stack):
  - Enforce that **Cognizant Technology Solutions** appears FIRST under the `EXPERIENCE` section, followed by **USF Graduate Researcher**.
  - Add explicit prompt rules in `rewrite_prompts.py` and `rewrite.py`.

### 2. Stack-Aware Project Section Pipeline
- **Java Target Applications**:
  - Do NOT replace or remove the Java project (`High-Throughput Financial Order Ledger` / `Configuration Management API Service`) from the base resume template.
  - Skip project section replacement when target stack is Java.
- **Non-Java Target Applications (AI, Python, Node)**:
  - Remove the template's Java project from `PROJECTS`.
  - Inject the two catalog projects from `backend/storage/Resources/projects.json` (Project 1: QA Assistant, Project 2: PR Doc Agent).
  - For **JS/Node/TypeScript** target roles, adapt the tech stacks of the two injected projects to Express.js, TypeScript, Node.js, Jest, and REST APIs.

### 3. Verification & Testing
- Add unit test cases in `backend/tests/test_final_pipeline.py` verifying:
  - Cognizant-first ordering for Java roles.
  - Java project preservation for Java roles.
  - Project replacement and Node/TypeScript tech stack adaptation for JS/Node roles.
- Execute full pytest suite (`python -m pytest backend/tests`).

## Non-Functional Requirements
- **ATS & Formatting Compliance**: Maintain valid LaTeX formatting, pipe separators, and strict compilation syntax.
