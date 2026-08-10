import re
import sys
from pathlib import Path

def remove_hyphens():
    tex_path = Path(r"d:\Projects\Resume Maker\resume.tex")
    
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace all hyphens between alphanumeric characters with a space
    # Example: "high-volume" -> "high volume", "sub-2s" -> "sub 2s"
    # Will not match "--" or "-10pt"
    # We do a while loop to handle overlapping matches like "state-by-state"
    prev_content = ""
    while prev_content != content:
        prev_content = content
        content = re.sub(r'([a-zA-Z0-9])-([a-zA-Z0-9])', r'\1 \2', content)
        
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Removed all compound hyphens from resume.tex")
    
if __name__ == "__main__":
    remove_hyphens()
    
    # Now sync to frontend
    import importlib.util
    sync_path = Path(r"d:\Projects\Resume Maker\scratch\sync_frontend.py")
    spec = importlib.util.spec_from_file_location("sync_frontend", sync_path)
    sync_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_module)
    sync_module.sync_resume()
