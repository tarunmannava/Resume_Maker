import docx
from pathlib import Path
import re

pairs = [
    ("ai", "generated_resumes/TarunMannava.docx", "backend/app/templates/archetypes/ai.tex"),
    ("node", "generated_resumes/TarunMannava_SE.docx", "backend/app/templates/archetypes/node.tex"),
    ("java", "generated_resumes/TarunMannava_SoftwareEngineer.docx", "backend/app/templates/archetypes/java.tex"),
    ("dotnet", "generated_resumes/TarunMannava_DotnetDeveloper.docx", "backend/app/templates/archetypes/dotnet.tex"),
    ("python", "generated_resumes/TarunMannava_SoftwareDeveloper.docx", "backend/app/templates/archetypes/python.tex"),
]

for stack, docx_p, tex_p in pairs:
    doc = docx.Document(docx_p)
    docx_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    tex = Path(tex_p).read_text(encoding="utf-8")
    
    print(f"=== {stack.upper()} ===")
    print(f"  Docx paras: {len(docx_paras)}")
    
    # Check key sections
    for sec in ["SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION"]:
        assert sec in tex, f"Missing section {sec} in {tex_p}"
    
    # Check bullet counts
    bullet_matches = re.findall(r"\\resumeItem\{(.*?)\}", tex)
    docx_bullets = [p for p in docx_paras if doc.paragraphs[docx_paras.index(p)].style.name.startswith("List")]
    print(f"  Tex bullets: {len(bullet_matches)} | Docx bullets: {len(docx_bullets)}")
    
    # Check projects
    project_matches = re.findall(r"\\resumeProject\{(.*?)\}", tex)
    print(f"  Tex projects: {len(project_matches)}")

print("\nAll 5 archetypes verified successfully!")
