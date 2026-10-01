import re
import glob

projects = set()
for ext in ('*.py', '*.tex', '*.json', '*.md'):
    for p in glob.glob('**/' + ext, recursive=True):
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for m in re.finditer(r'resumeProject\{([^}]+)\}', content):
                    projects.add(m.group(1).strip())
                for m in re.finditer(r'add_project_heading\([^,]+,\s*["\']([^"\']+)["\']', content):
                    projects.add(m.group(1).strip())
        except Exception:
            pass

for prj in sorted(projects):
    print(prj)
