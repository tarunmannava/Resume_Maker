# Implementation Plan: Final Resume Adaptation & Stack-Aware Project Pipeline

## Phase 1: Pipeline Rules & Project Preservation Logic
- [x] Task: Update `backend/app/services/rewrite.py` to bypass project section replacement when target stack is Java.
- [x] Task: Update `backend/app/services/rewrite_prompts.py` and `rewrite.py` to enforce Cognizant-first experience section ordering for Java roles.
- [x] Task: Adapt injected catalog projects to Node/TypeScript stack when target stack is JS/Node.

## Phase 2: Unit Testing & Pipeline Validation
- [x] Task: Create `backend/tests/test_final_pipeline.py` to test Cognizant-first ordering, Java project preservation, and JS project stack adaptation.
- [x] Task: Run full pytest suite across `backend/tests` to verify 100% pass rate.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).
