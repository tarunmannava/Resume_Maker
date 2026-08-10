import re
from pathlib import Path

def sync_resume():
    root = Path(r"d:\Projects\Resume Maker")
    tex_file = root / "resume.tex"
    ts_file = root / "frontend" / "src" / "lib" / "constants.ts"
    
    with open(tex_file, "r", encoding="utf-8") as f:
        tex_content = f.read()
        
    # Escape backslashes for TS template literal
    tex_content = tex_content.replace("\\", "\\\\")
        
    with open(ts_file, "r", encoding="utf-8") as f:
        ts_content = f.read()
        
    # Find the start and end of the string
    start_str = "export const sampleResume = `"
    end_str = "`;\n"
    
    start_idx = ts_content.find(start_str)
    # find the very next semicolon after start_idx
    end_idx = ts_content.find("`;", start_idx) + 2
    
    if start_idx != -1 and end_idx != -1:
        new_ts_content = ts_content[:start_idx + len(start_str)] + tex_content + ts_content[end_idx - 2:]
    else:
        print("Could not find sampleResume block.")
        return
    
    with open(ts_file, "w", encoding="utf-8") as f:
        f.write(new_ts_content)
        
    print("Synced resume.tex to constants.ts!")

if __name__ == "__main__":
    sync_resume()
