# Operational Workflow: Resume Maker

## Development Protocol
1. **Test-Driven Development & Validation**:
   - Run backend pytest suites (`pytest backend/tests`) to ensure keyword scoring, LaTeX parsing, project RAG, and rewrite pipelines remain regression-free.
   - Run frontend build/lint checks (`npm run build`) before pushing changes.
2. **Commit Hygiene**:
   - Commits follow conventional commit syntax: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
3. **Safety & Risk Mitigation**:
   - Never commit API keys (`.env` files are gitignored).
   - Ensure project injection and skill sanitization guards run on all LLM outputs before returning response.
