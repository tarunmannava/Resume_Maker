import json
import sys
from pathlib import Path
sys.path.append(str(Path(r"D:\Projects\Resume Maker\backend")))
from app.services.project_rag import get_relevant_projects
jd_text = """
Responsibilities
Understand and modify application(s) using Linux, Windows, C++, React, CSS, Python, etc.
Understand, create, and modify software and/or test documentation
Support development, evaluation, system/software integration, and test
Support unit testing and system/software integration test including test plan/procedure development
Ensure software products are delivered on-time with high quality and detail
Software development will be performed within an Agile Scrum environment following software engineering standards and applying common tools

Qualifications
HS 3-4 Years
Pursuing a BS in Computer Science, Computer Engineering, or closely related field
Object-oriented programming experience in C++ and/or Java
Familiar with Integrated Development Environments such as Eclipse, and tools such as Jira, Bamboo and Git
Strong problem-solving and troubleshooting skills
Effective written and verbal skills
Able to work and thrive in both individual and team coding environments with mentors
Experience with development under UNIX- or Linux-based systems is a plus
Experience in web development, and/or databases is a plus
"""

if __name__ == "__main__":
    print("Testing RAG retrieval for specific JD...")
    # Get top 8 projects to see the full ranking and scores
    results = get_relevant_projects(jd_text, top_k=8)
    print("\n--- RAG RANKING ---")
    for i, res in enumerate(results):
        print(f"{i+1}. {res['id']}")
        print(f"   Keys: {list(res.keys())}")
