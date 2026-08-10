import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
from app.services.rewrite import rewrite_resume
from app.models.schemas import RewriteRequest

def main():
    resume_path = r"D:\Projects\Resume Maker\resume.tex"
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_latex = f.read()
        
    job_description = """
    Senior Java Backend Engineer
    We are looking for a backend engineer who has built production Java web applications.
    You should have experience with Spring Boot, PostgreSQL, and Hibernate.
    Experience with Issue Trackers, Jira integrations, or Workflow Management is a huge plus!
    You should also know distributed job processing, async tasks, Kafka, Redis, and cron scheduling.
    """
    
    req = RewriteRequest(
        job_description=job_description,
        resume_latex=resume_latex,
        role_name="Senior Java Backend Engineer",
        target_match_threshold=80,
        rewrite_mode="transferable",
        align_titles=True
    )
    
    print("Testing Rewrite Pipeline with RAG...")
    try:
        response = rewrite_resume(req)
        print("Pipeline succeeded!")
        print("Changes made:")
        for change in response.changes_made:
            print(f" - {change}")
            
        print("\nWarnings:")
        for warning in response.warnings:
            print(f" ! {warning}")
            
        print("\nExtracted projects snippet from output:")
        # Find where PROJECTS is located
        idx = response.rewritten_latex.find("PROJECTS")
        if idx != -1:
            print(response.rewritten_latex[idx-10:idx+800])
            
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
