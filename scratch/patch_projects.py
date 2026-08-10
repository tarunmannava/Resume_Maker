import json
import os
from pathlib import Path

def patch_projects():
    projects_file = Path(r"D:\Projects\Resume Maker\backend\storage\resources\projects.json")
    
    with open(projects_file, "r", encoding="utf-8") as f:
        projects = json.load(f)
        
    for p in projects:
        # 1. Fix Nexus ID collision
        if p["name"] == "Nexus" and p["id"] == "project_1":
            p["id"] = "nexus_job_processor"
            
        # 2. Fix Fraud F1-score exaggeration
        if p["id"] == "project_5":
            p["bullets"][0] = p["bullets"][0].replace("0.94 F1-score", "0.94 ROC-AUC")
            p["extra_context"] = p["extra_context"].replace("F1-score", "ROC-AUC")
            
        # 3. Modernize Trackr
        if p["id"] == "trackr_issue_tracker":
            # Update Tech Stack
            old_stack = set(p["tech_stack"])
            to_remove = {"JSP", "Servlets", "HTML", "CSS", "Bootstrap"}
            to_add = ["React", "TypeScript", "Tailwind CSS", "REST APIs", "Node.js"]
            new_stack = [tech for tech in p["tech_stack"] if tech not in to_remove]
            for tech in to_add:
                if tech not in new_stack:
                    new_stack.insert(new_stack.index("PostgreSQL"), tech)
            p["tech_stack"] = new_stack
            
            # Update Bullets
            p["bullets"][0] = p["bullets"][0].replace(
                "using Spring Boot, Spring MVC, Spring Security, and PostgreSQL", 
                "with a React/TypeScript frontend and a Spring Boot REST API backend"
            )
            
            # Update Context
            p["extra_context"] = p["extra_context"].replace(
                "JSP/Servlet-rendered views", 
                "a React Single Page Application (SPA)"
            )
            p["extra_context"] = p["extra_context"].replace(
                "user submits request via JSP form or URL -> DispatcherServlet routes to Spring MVC Controller -> Controller calls Service layer",
                "React frontend makes async Axios requests -> Spring Boot REST Controller validates JSON payload -> Controller calls Service layer"
            )
            p["extra_context"] = p["extra_context"].replace(
                "Response rendered via JSP view",
                "Controller returns JSON response to React client"
            )
            p["extra_context"] = p["extra_context"].replace(
                "View (JSP templates)",
                "Frontend (React components, Tailwind CSS styling, Axios state management)"
            )
            
    with open(projects_file, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)
        
    print("Successfully patched projects.json!")

if __name__ == "__main__":
    patch_projects()
