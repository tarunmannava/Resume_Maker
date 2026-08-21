# Implementation Plan: DOCX Generator Complete Rewrite

## Phase 1: Lexer, Parser & Token Stream
- [ ] Task 1.1: Build robust LaTeX macro expansion and AST/token stream parser for LaTeX resume body in `backend/app/services/docx.py`.
- [ ] Task 1.2: Add unit tests for tokenizer and macro unwrapper in `backend/tests/test_docx.py`.

## Phase 2: Header, Contact, & Section Layout Engine
- [ ] Task 2.1: Implement header parsing with centered name, bullet-delimited contact runs, clean hyperlink embedding (`mailto:`, web URLs), and optional summary paragraph.
- [ ] Task 2.2: Implement section heading rendering with bottom border rule and empty-section suppression (e.g. empty CERTIFICATIONS).

## Phase 3: Experience, Education, Projects, & Bullet Rendering
- [ ] Task 3.1: Implement `\resumeSubheading` / `\resumeSubSubheading` rendering with tab-stop right-aligned dates for Experience and Education.
- [ ] Task 3.2: Implement `\resumeProject` / `\resumeProjectHeading` rendering with project links, title, pipe separator, tech stack, and nested bullets.
- [ ] Task 3.3: Implement recursive inline run formatter for `\textbf`, `\textit`, `\emph`, `\underline`, `\href`, and clean text runs.

## Phase 4: Verification & Test Suite
- [ ] Task 4.1: Run full test suite across diverse resume templates and edge cases in `backend/tests/test_docx.py`.
