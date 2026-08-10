# Implementation Plan: Canonical LaTeX SKILLS Templates Storage & Dynamic Integration Engine

## Phase 1: Canonical Storage & Data Loader
- [x] Task: Create `backend/storage/Resources/skills_templates.json` containing the 4 canonical LaTeX SKILLS section templates.
- [x] Task: Implement `backend/app/services/skills_data.py` to load and parse templates by stack key (`java`, `ai`, `python`, `node`).
- [x] Task: Write unit tests in `backend/tests/test_canonical_skills.py` for data loading and structure.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).

## Phase 2: Backend Skills Adaptation Engine Integration
- [x] Task: Update `backend/app/services/latex_skills.py` to use canonical templates as structural baselines for target role/stack.
- [x] Task: Implement JD-aware pruning and item selection logic while maintaining template category headers and pipe separators.
- [x] Task: Update `backend/app/services/rewrite.py` post-processing pipeline to invoke the template-based skill adapter.
- [x] Task: Write unit tests verifying end-to-end SKILLS adaptation across Java, AI, Python, and Node targets.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).

## Phase 3: Validation & Test Suite Check
- [x] Task: Run full pytest suite across `backend/tests` to verify zero regressions.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md).
