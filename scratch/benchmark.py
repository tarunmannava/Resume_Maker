import time
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_JOB = """
Required: Python, Django, PostgreSQL, REST APIs, AWS.
Preferred: React or Angular, Docker, CI/CD.
We value backend engineers who can build scalable services and collaborate across teams.
"""

SAMPLE_RESUME = r"""
\documentclass[a4paper,10pt]{article}
\begin{document}
\section{EXPERIENCE}
\textbf{Software Engineer} \\
\textit{Built backend services using Python, Java, and Spring Boot.}
\end{document}
"""

def benchmark_endpoint(method, endpoint, payload=None, n=1):
    times = []
    successes = 0
    
    print(f"Benchmarking {method} {endpoint} (runs: {n})...")
    for _ in range(n):
        start = time.time()
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json=payload)
        
        elapsed = time.time() - start
        times.append(elapsed)
        if response.status_code == 200:
            successes += 1
        else:
            print(f"Error {response.status_code}: {response.text}")
            
    avg_time = sum(times) / len(times)
    print(f"  -> Avg time: {avg_time:.4f}s | Success rate: {successes}/{n}")
    return avg_time

def main():
    print("Starting Efficiency Benchmark...\n")
    
    # 1. Health check
    benchmark_endpoint("GET", "/api/health", n=3)
    
    # 2. Analyze Job
    job_payload = {
        "job_description": SAMPLE_JOB,
        "company_context": ""
    }
    benchmark_endpoint("POST", "/api/analyze-job", payload=job_payload, n=3)
    
    # 3. Analyze Resume
    resume_payload = {
        "resume_latex": SAMPLE_RESUME
    }
    benchmark_endpoint("POST", "/api/analyze-resume", payload=resume_payload, n=3)
    
    # 4. Score
    score_payload = {
        "job_description": SAMPLE_JOB,
        "resume_latex": SAMPLE_RESUME,
        "rewrite_mode": "strict",
        "confirmed_skills": []
    }
    benchmark_endpoint("POST", "/api/score", payload=score_payload, n=3)
    
    # Optional: We can test rewrite, but it calls the LLM, so let's just do 1 run.
    rewrite_payload = {
        "job_description": SAMPLE_JOB,
        "resume_latex": SAMPLE_RESUME,
        "candidate_name": "Test User",
        "company_name": "Test Co",
        "role_name": "Backend Dev",
        "rewrite_mode": "strict",
        "target_match_threshold": 75,
        "confirmed_skills": [],
        "banned_skills": [],
        "align_titles": False,
        "selected_industry": "Don't know",
        "selected_role_category": "Software Engineer"
    }
    benchmark_endpoint("POST", "/api/rewrite", payload=rewrite_payload, n=1)

if __name__ == "__main__":
    main()
