import os
import sys
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Add backend directory to sys.path so we can import config
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
from app.core.config import get_settings
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

class ProjectData(BaseModel):
    id: str = Field(description="A unique identifier, e.g., 'project_1' or 'nexus_job_platform'")
    name: str = Field(description="The short name or title of the project")
    title: str = Field(description="The full role-framed title of the project")
    target_roles: list[str] = Field(description="A list of target roles this project applies to")
    tech_stack: list[str] = Field(description="A list of technologies used in the project")
    bullets: list[str] = Field(description="A list of 3-5 bullet points describing the project in X-Y-Z metric format")
    description: str = Field(description="A short 1-2 sentence description of the project")
    extra_context: str = Field(description="A detailed summary of the architecture, features, workflows, and evaluation metrics described in the raw text, ensuring no technical details are lost.")

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def structure_project_with_ai(client: OpenAI, model: str, raw_text: str) -> dict | None:
    prompt = f"""
    Extract the project details from the following raw PDF text into a JSON object.
    Preserve all hard metrics, numbers, and technical terms.
    If the text has 'Resume Bullets', use those exactly for the 'bullets' array. 
    Otherwise, adapt the core features into 3-4 professional resume bullets.
    
    RAW TEXT:
    {raw_text}
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise data extraction tool. You must respond with raw JSON that strictly adheres to the requested schema. Do NOT wrap the JSON in markdown fences."},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "project_data",
                    "schema": ProjectData.model_json_schema()
                }
            },
            temperature=0.1
        )
        # Some providers wrap in markdown even with json_schema, so strip it
        content = completion.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].strip() == "```": lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def main():
    settings = get_settings()
    if not settings.openai_api_key and not settings.openrouter_api_key:
        print("OPENAI_API_KEY is not set.")
        return

    client = OpenAI(
        api_key=settings.openai_api_key or settings.openrouter_api_key,
        base_url=settings.openai_base_url
    )
    model = settings.openai_model

    resources_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'storage', 'resources')
    output_file = os.path.join(resources_dir, 'projects.json')

    all_projects = []

    for filename in os.listdir(resources_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(resources_dir, filename)
            print(f"Processing {filename}...")
            
            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text.strip():
                print(f"  Warning: No text extracted from {filename}")
                continue
                
            structured_data = structure_project_with_ai(client, model, raw_text)
            if structured_data:
                structured_data["source_file"] = filename
                all_projects.append(structured_data)
                print(f"  -> Successfully structured: {structured_data.get('title')}")
            else:
                print(f"  -> Failed to structure {filename}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_projects, f, indent=2, ensure_ascii=False)
        
    print(f"\nDone! Wrote {len(all_projects)} projects to {output_file}")

if __name__ == "__main__":
    main()
