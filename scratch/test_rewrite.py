import os
from dotenv import load_dotenv
# Load env variables before importing config
load_dotenv("backend/.env")

from backend.app.services.rewrite import rewrite_resume
from backend.app.models.schemas import RewriteRequest

sample_resume = r"""\section{Skills}
Java, Python, React, PostgreSQL, AWS

\section{Experience}
\resumeItem{Built Java backend services with REST APIs, authentication, PostgreSQL, and performance-focused request handling.}
\resumeItem{Built React dashboards with reusable components, client-side routing, and API integration.}"""

sample_job = """Required: Python, Django, PostgreSQL, REST APIs, AWS.
Preferred: React or Angular, Docker, CI/CD, Cursor, Claude Code.
We value backend engineers who can build scalable services and collaborate across teams."""

req = RewriteRequest(
    job_description=sample_job,
    resume_latex=sample_resume,
    candidate_name="Tarun Kumar",
    company_name="Google",
    role_name="Software Engineer",
    rewrite_mode="transferable",
    target_match_threshold=75,
    confirmed_skills=[],
    banned_skills=[],
)

print("Calling rewrite_resume...")
try:
    res = rewrite_resume(req)
    print("STATUS: SUCCESS")
    print("Match Score:", res.match_score)
    print("Warnings:", res.warnings)
    print("Changes Made:", res.changes_made)
    print("Rewritten LaTeX length:", len(res.rewritten_latex))
    print("Entire rewritten LaTeX:\n", res.rewritten_latex)
except Exception as e:
    print("STATUS: FAILED")
    print("Error:", e)
    import traceback
    traceback.print_exc()
