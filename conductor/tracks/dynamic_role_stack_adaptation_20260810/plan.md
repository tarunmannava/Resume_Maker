# Implementation Plan: Dynamic Base Resume & Stack-Aware Experience/Project Adaptation Engine

## Phase 1: Backend Data & Classifier Adaptation
- [x] Task: Validate `projects.json` and `projects_data.py` catalog for 2 AI + 1 Java project entries.
- [x] Task: Extend `job_analyzer.py` / `rewrite_strategy.py` to auto-detect target stack (`java`, `node`, `python`) from job description.
- [x] Task: Implement Cognizant experience Java guardrail in `rewrite.py` to prevent language changes from Java.
- [x] Task: Implement USF experience dynamic re-framing logic in `project_framing.py` for target stacks (`java`, `node`, `python`).
- [x] Task: Write backend unit tests in `tests/test_stack_adaptation.py` verifying stack detection, Cognizant Java guardrail, and USF experience adaptation.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).

## Phase 2: Frontend Role Selector & Manual Stack Override UI
- [x] Task: Update role selector options in `App.tsx` / `constants.ts` to `Java Developer` and `AI Engineer / Software Engineer`.
- [x] Task: Add interactive stack toggle pills (`Auto: Node.js`, `Python`, `Java`) allowing user override.
- [x] Task: Pass `selected_role` and `selected_stack_override` payload parameters to `/api/rewrite`.
- [x] Task: Verify end-to-end integration across frontend state and backend response.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).

## Phase 3: Technical Skills & Projects Injection Refinement
- [x] Task: Update `latex_skills.py` to reorder and sanitize skill lines based on role (`Java Developer` vs `AI Engineer` vs `Software Engineer`).
- [x] Task: Verify deterministic project injection in `latex_projects.py` for Java vs Node vs Python targets.
- [x] Task: Run full pytest suite across `backend/tests`.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).
