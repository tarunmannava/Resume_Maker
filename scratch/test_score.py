from backend.app.services.scoring import score_keywords
from backend.app.services.keyword_extractor import extract_keywords
from backend.app.services.latex import latex_to_text

sample_resume = r"""\section{Skills}
Java, Python, React, PostgreSQL, AWS

\section{Experience}
\resumeItem{Built Java backend services with REST APIs, authentication, PostgreSQL, and performance-focused request handling.}
\resumeItem{Built React dashboards with reusable components, client-side routing, and API integration.}"""

sample_job = """Required: Python, Django, PostgreSQL, REST APIs, AWS.
Preferred: React or Angular, Docker, CI/CD.
We value backend engineers who can build scalable services and collaborate across teams."""

resume_text = latex_to_text(sample_resume)
job_keywords = extract_keywords(sample_job, job_context=True)

print("Job Keywords:", [item.term for item in job_keywords])
print("Resume Text:", resume_text)

score_res = score_keywords(
    job_keywords,
    resume_text,
    target_threshold=75,
    rewrite_mode="transferable"
)
print("Score:", score_res.match_score)
print("Matched:", [m.term for m in score_res.matched_keywords])
print("Missing:", [m.term for m in score_res.missing_keywords])
print("Unsupported:", [u.term for u in score_res.unsupported_keywords])
