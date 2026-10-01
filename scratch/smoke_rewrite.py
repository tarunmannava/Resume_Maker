import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.config import get_settings
from backend.app.models.schemas import RewriteRequest
from backend.app.services.pdf import compile_latex_to_docx
from backend.app.services.rewrite import get_archetype_latex, rewrite_resume

settings = get_settings()
print("AI provider:", settings.ai_provider, "| model:", settings.openai_model, "| key set:", bool(settings.openai_api_key))

flagged = json.loads(Path(r"C:\Users\tarun\Documents\resumes\flagged.json").read_text(encoding="utf-8"))
job = next(j for j in flagged if not j.get("primary_stack") and len(j.get("jd") or "") > 1500)
print(f"Job: {job['title']} @ {job['company']} | JD chars: {len(job['jd'])}")
print("JD preview:", job["jd"][:400].replace("\n", " "))

base_latex = (Path(__file__).resolve().parents[1] / "Tarun_Mannava_Resume.tex").read_text(encoding="utf-8")

start = time.time()
result = rewrite_resume(
    RewriteRequest(
        job_description=job["jd"],
        resume_latex=base_latex,
        candidate_name="Tarun Mannava",
        company_name=job["company"],
        role_name=job["title"],
        rewrite_mode="transferable",
        target_match_threshold=88,
    )
)
print(f"Rewrite took {time.time() - start:.1f}s | match score: {result.match_score} | target met: {result.target_met}")
print("Missing keywords:", [k.term for k in result.missing_keywords][:15])
print("Warnings:", result.warnings[:8])
print("Changes:", result.changes_made[:5])

comp = compile_latex_to_docx(result.rewritten_latex, "Tarun Mannava", job["company"], job["title"])
print("DOCX success:", comp.success, "| path:", comp.docx_path, "| errors:", comp.errors)
