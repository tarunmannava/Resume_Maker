import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app.models.schemas import RewriteRequest
from app.services.rewrite import rewrite_resume

SAMPLE_JOB = """
Software Engineer, Backend
Required:
- 2+ years of experience in backend development using Java and Spring Boot.
- Strong knowledge of SQL and NoSQL databases (PostgreSQL, MongoDB).
- Experience with cloud platforms like AWS or Azure.
- Familiarity with CI/CD, Docker, and Kubernetes.
Preferred:
- Experience with real-time distributed systems.
- Familiarity with Python or Node.js.
"""

def main():
    resume_path = os.path.join(os.path.dirname(__file__), '..', 'resume.tex')
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_latex = f.read()

    request = RewriteRequest(
        job_description=SAMPLE_JOB,
        resume_latex=resume_latex,
        candidate_name="Tarun Mannava",
        company_name="Tech Corp",
        role_name="Software Engineer",
        rewrite_mode="strict",
        target_match_threshold=80,
        confirmed_skills=[],
        banned_skills=[],
        align_titles=True,
        selected_industry="Don't know",
        selected_role_category="Software Engineer"
    )

    print("Running rewrite_resume...")
    response = rewrite_resume(request)
    
    out_path = os.path.join(os.path.dirname(__file__), 'rewritten_resume.tex')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(response.rewritten_latex)
        
    print(f"Done. Wrote to {out_path}")

if __name__ == "__main__":
    main()
